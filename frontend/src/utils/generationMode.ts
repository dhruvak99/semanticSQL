export type GenerationMode = 'LLM' | 'Rule';

export function normalizeGenerationMode(value: string): GenerationMode {
  return value.toUpperCase() === 'LLM' ? 'LLM' : 'Rule';
}
