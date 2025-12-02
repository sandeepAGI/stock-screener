import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useWeights } from '../hooks/useWeights';
import type { Weights } from '../hooks/useWeights';

interface WeightsContextType {
  weights: Weights;
  normalizedWeights: {
    fundamental: number;
    quality: number;
    growth: number;
    sentiment: number;
  };
  setWeight: (key: keyof Weights, value: number) => void;
  resetWeights: () => void;
  isDefault: boolean;
  calculateCustomScore: (scores: {
    fundamental: number | null;
    quality: number | null;
    growth: number | null;
    sentiment: number | null;
  }) => number;
  DEFAULT_WEIGHTS: Weights;
}

const WeightsContext = createContext<WeightsContextType | null>(null);

export function WeightsProvider({ children }: { children: ReactNode }) {
  const weightsState = useWeights();

  return (
    <WeightsContext.Provider value={weightsState}>
      {children}
    </WeightsContext.Provider>
  );
}

export function useWeightsContext() {
  const context = useContext(WeightsContext);
  if (!context) {
    throw new Error('useWeightsContext must be used within a WeightsProvider');
  }
  return context;
}
