import { useState, useCallback, useMemo } from 'react';

export interface Weights {
  fundamental: number;
  quality: number;
  growth: number;
  sentiment: number;
}

const DEFAULT_WEIGHTS: Weights = {
  fundamental: 40,
  quality: 25,
  growth: 20,
  sentiment: 15,
};

export function useWeights() {
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);

  const normalizedWeights = useMemo(() => {
    const total = weights.fundamental + weights.quality + weights.growth + weights.sentiment;
    if (total === 0) return { fundamental: 0.25, quality: 0.25, growth: 0.25, sentiment: 0.25 };
    return {
      fundamental: weights.fundamental / total,
      quality: weights.quality / total,
      growth: weights.growth / total,
      sentiment: weights.sentiment / total,
    };
  }, [weights]);

  const setWeight = useCallback((key: keyof Weights, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetWeights = useCallback(() => {
    setWeights(DEFAULT_WEIGHTS);
  }, []);

  const isDefault = useMemo(() => {
    return (
      weights.fundamental === DEFAULT_WEIGHTS.fundamental &&
      weights.quality === DEFAULT_WEIGHTS.quality &&
      weights.growth === DEFAULT_WEIGHTS.growth &&
      weights.sentiment === DEFAULT_WEIGHTS.sentiment
    );
  }, [weights]);

  // Calculate custom composite score
  const calculateCustomScore = useCallback(
    (scores: { fundamental: number | null; quality: number | null; growth: number | null; sentiment: number | null }) => {
      const f = scores.fundamental ?? 0;
      const q = scores.quality ?? 0;
      const g = scores.growth ?? 0;
      const s = scores.sentiment ?? 0;
      return (
        f * normalizedWeights.fundamental +
        q * normalizedWeights.quality +
        g * normalizedWeights.growth +
        s * normalizedWeights.sentiment
      );
    },
    [normalizedWeights]
  );

  return {
    weights,
    normalizedWeights,
    setWeight,
    resetWeights,
    isDefault,
    calculateCustomScore,
    DEFAULT_WEIGHTS,
  };
}
