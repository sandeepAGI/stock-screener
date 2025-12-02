/**
 * StockAnalyzer Pro - Electron Main Process
 *
 * Responsibilities:
 * - Start Python FastAPI backend on app launch
 * - Open React frontend in BrowserWindow
 * - Handle app lifecycle (quit, minimize, etc.)
 * - Manage Python process cleanup
 */

const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');

// Configuration
const isDev = process.argv.includes('--dev');
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;

// Global references
let mainWindow = null;
let pythonProcess = null;
let splashWindow = null;

// Paths
function getResourcePath() {
  if (isDev) {
    return path.join(__dirname, '..');
  }
  return process.resourcesPath;
}

function getPythonPath() {
  if (isDev) {
    // In development, use the virtual environment
    return path.join(getResourcePath(), 'venv', 'bin', 'python');
  }
  // In production, use bundled Python
  return path.join(getResourcePath(), 'python', 'bin', 'python3');
}

function getBackendPath() {
  if (isDev) {
    return path.join(getResourcePath(), 'backend', 'main.py');
  }
  return path.join(getResourcePath(), 'backend', 'main.py');
}

function getDataPath() {
  // User data directory for database
  const userDataPath = app.getPath('userData');
  const dataPath = path.join(userDataPath, 'data');

  // Create directory if it doesn't exist
  if (!fs.existsSync(dataPath)) {
    fs.mkdirSync(dataPath, { recursive: true });
  }

  return dataPath;
}

function getDatabasePath() {
  return path.join(getDataPath(), 'stock_data.db');
}

// Check if port is available
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close();
      resolve(true);
    });
    server.listen(port);
  });
}

// Wait for backend to be ready
async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}/api/health`);
      if (response.ok) {
        console.log('Backend is ready');
        return true;
      }
    } catch (error) {
      // Backend not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  return false;
}

// Start Python backend
async function startBackend() {
  const pythonPath = getPythonPath();
  const backendPath = getBackendPath();

  console.log('Starting Python backend...');
  console.log('Python path:', pythonPath);
  console.log('Backend path:', backendPath);

  // Set environment variables
  const env = {
    ...process.env,
    PYTHONPATH: getResourcePath(),
    STOCKANALYZER_DATA_DIR: getDataPath(),
    STOCKANALYZER_DB_PATH: getDatabasePath(),
  };

  // Check if Python exists
  if (!fs.existsSync(pythonPath)) {
    console.error('Python not found at:', pythonPath);

    // Try system Python as fallback in dev mode
    if (isDev) {
      pythonProcess = spawn('python3', ['-m', 'uvicorn', 'backend.main:app',
        '--host', '127.0.0.1',
        '--port', String(BACKEND_PORT),
        '--reload'
      ], {
        cwd: getResourcePath(),
        env,
        stdio: ['ignore', 'pipe', 'pipe']
      });
    } else {
      throw new Error('Python runtime not found');
    }
  } else {
    pythonProcess = spawn(pythonPath, ['-m', 'uvicorn', 'backend.main:app',
      '--host', '127.0.0.1',
      '--port', String(BACKEND_PORT)
    ], {
      cwd: getResourcePath(),
      env,
      stdio: ['ignore', 'pipe', 'pipe']
    });
  }

  // Handle output
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  pythonProcess.on('error', (error) => {
    console.error('Failed to start backend:', error);
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Backend exited with code ${code}`);
    pythonProcess = null;
  });

  // Wait for backend to be ready
  const ready = await waitForBackend();
  if (!ready) {
    throw new Error('Backend failed to start');
  }

  return true;
}

// Stop Python backend
function stopBackend() {
  if (pythonProcess) {
    console.log('Stopping Python backend...');

    // Try graceful shutdown first
    pythonProcess.kill('SIGTERM');

    // Force kill after 5 seconds
    setTimeout(() => {
      if (pythonProcess) {
        pythonProcess.kill('SIGKILL');
        pythonProcess = null;
      }
    }, 5000);
  }
}

// Create splash screen
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Simple HTML splash screen
  splashWindow.loadURL(`data:text/html,
    <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            border-radius: 10px;
          }
          h1 { margin: 0 0 10px 0; font-size: 24px; }
          .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #4dabf7;
            animation: spin 1s ease-in-out infinite;
            margin-top: 20px;
          }
          @keyframes spin { to { transform: rotate(360deg); } }
          .status { margin-top: 15px; font-size: 14px; opacity: 0.8; }
        </style>
      </head>
      <body>
        <h1>StockAnalyzer Pro</h1>
        <p>Stock Analysis & Outlier Detection</p>
        <div class="spinner"></div>
        <p class="status">Starting backend...</p>
      </body>
    </html>
  `);
}

// Create main window
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    show: false,
    title: 'StockAnalyzer Pro',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load frontend
  if (isDev) {
    // In development, connect to Vite dev server
    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load built frontend
    mainWindow.loadFile(path.join(getResourcePath(), 'frontend', 'dist', 'index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create menu
function createMenu() {
  const template = [
    {
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        {
          label: 'Preferences...',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            // TODO: Open preferences window
          }
        },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        { role: 'front' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/sandeepAGI/stock-screener');
          }
        },
        {
          label: 'Report Issue',
          click: () => {
            shell.openExternal('https://github.com/sandeepAGI/stock-screener/issues');
          }
        }
      ]
    }
  ];

  // Add dev tools menu in development
  if (isDev) {
    template[2].submenu.push(
      { type: 'separator' },
      { role: 'toggleDevTools' }
    );
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC handlers
function setupIPC() {
  // Get app info
  ipcMain.handle('get-app-info', () => ({
    version: app.getVersion(),
    dataPath: getDataPath(),
    isDev
  }));

  // Get backend URL
  ipcMain.handle('get-backend-url', () => `http://127.0.0.1:${BACKEND_PORT}`);

  // Open external link
  ipcMain.handle('open-external', (event, url) => {
    shell.openExternal(url);
  });
}

// App events
app.whenReady().then(async () => {
  console.log('App starting...');
  console.log('Development mode:', isDev);

  // Create splash screen
  createSplashWindow();

  try {
    // Start backend
    await startBackend();

    // Create main window and menu
    createMenu();
    createMainWindow();
    setupIPC();

  } catch (error) {
    console.error('Failed to start app:', error);

    if (splashWindow) {
      splashWindow.close();
    }

    dialog.showErrorBox(
      'Startup Error',
      `Failed to start StockAnalyzer Pro:\n\n${error.message}\n\nPlease check the console for details.`
    );

    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createMainWindow();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('will-quit', () => {
  stopBackend();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  stopBackend();
});
