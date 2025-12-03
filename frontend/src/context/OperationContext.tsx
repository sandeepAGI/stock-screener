import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { api } from '../api/client';

type OperationType = 'data' | 'sentiment' | 'calculate' | null;

interface OperationState {
  type: OperationType;
  status: string;
  isActive: boolean;
  progress?: number;
  currentSymbol?: string;
}

interface OperationContextType {
  operation: OperationState;
  setOperation: (type: OperationType, status: string) => void;
  clearOperation: () => void;
  refreshStatus: () => Promise<void>;
}

const OperationContext = createContext<OperationContextType | null>(null);

export function OperationProvider({ children }: { children: ReactNode }) {
  const [operation, setOperationState] = useState<OperationState>({
    type: null,
    status: '',
    isActive: false,
  });

  const setOperation = useCallback((type: OperationType, status: string) => {
    setOperationState({
      type,
      status,
      isActive: type !== null,
    });
  }, []);

  const clearOperation = useCallback(() => {
    setOperationState({
      type: null,
      status: '',
      isActive: false,
    });
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      // Check data refresh status
      const dataStatus = await api.getDataStatus();
      if (dataStatus.is_collecting) {
        setOperationState({
          type: 'data',
          status: `Refreshing data: ${dataStatus.current_symbol || 'Starting...'}`,
          isActive: true,
          progress: dataStatus.progress,
          currentSymbol: dataStatus.current_symbol || undefined,
        });
        return;
      }

      // Check sentiment status
      const sentimentStatus = await api.getSentimentStatus();
      if (sentimentStatus.status === 'processing') {
        setOperationState({
          type: 'sentiment',
          status: `Processing sentiment: ${sentimentStatus.completed_items}/${sentimentStatus.total_items}`,
          isActive: true,
          progress: sentimentStatus.progress,
        });
        return;
      }

      // Check calculation status
      try {
        const calcStatus = await api.getCalculationStatus();
        if (calcStatus.is_calculating) {
          setOperationState({
            type: 'calculate',
            status: `Calculating: ${calcStatus.current_symbol || 'Starting...'}`,
            isActive: true,
            progress: calcStatus.progress,
            currentSymbol: calcStatus.current_symbol,
          });
          return;
        }
      } catch {
        // Calculation status endpoint might not exist, ignore
      }

      // Nothing active - clear if we were showing something
      if (operation.isActive) {
        // Keep the last status for a moment to show completion
        setOperationState(prev => ({
          ...prev,
          isActive: false,
          status: prev.status.includes('Error') ? prev.status : 'Completed',
        }));
      }
    } catch (error) {
      console.error('Error refreshing operation status:', error);
    }
  }, [operation.isActive]);

  // Poll for status updates
  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 3000);
    return () => clearInterval(interval);
  }, [refreshStatus]);

  return (
    <OperationContext.Provider value={{ operation, setOperation, clearOperation, refreshStatus }}>
      {children}
    </OperationContext.Provider>
  );
}

export function useOperationContext() {
  const context = useContext(OperationContext);
  if (!context) {
    throw new Error('useOperationContext must be used within an OperationProvider');
  }
  return context;
}
