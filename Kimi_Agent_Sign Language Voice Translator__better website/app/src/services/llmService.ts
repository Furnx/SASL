/**
 * LLM Service for Sentence Refinement
 *
 * Takes raw predicted words from the sign language model and refines them
 * into proper, grammatically correct sentences.
 *
 * In backend mode: calls the Python FastAPI /api/refine endpoint (which uses
 * OpenAI via LangChain server-side — API key never exposed to frontend).
 *
 * In mock mode: applies basic local refinement as a fallback.
 */

export interface RefinementResult {
  originalText: string;
  refinedText: string;
  isComplete: boolean;
}

class LLMService {
  private apiEndpoint: string = '/api/refine'; // Proxied to backend
  private backendBase: string = ''; // Resolved base URL
  private backendAvailable: boolean = false;

  /**
   * Initialize the LLM service.
   * Tries proxied URL first, then direct backend URL as fallback.
   */
  async initialize(): Promise<void> {
    // Try the Vite-proxied URL first
    const urls = ['/api/health', 'http://localhost:8000/api/health'];

    for (const url of urls) {
      try {
        const resp = await fetch(url, { signal: AbortSignal.timeout(3000) });
        if (resp.ok) {
          const data = await resp.json();
          this.backendAvailable = true;

          // Set the base URL for future API calls
          if (url.startsWith('http')) {
            this.backendBase = 'http://localhost:8000';
            this.apiEndpoint = `${this.backendBase}/api/refine`;
          }

          console.log(
            `✅ LLM service connected to backend via ${url} (LLM available: ${data.llm_available})`
          );
          return;
        }
      } catch (err) {
        console.log(`LLM health check failed for ${url}:`, err);
      }
    }

    this.backendAvailable = false;
    console.warn('⚠️ Backend not available — LLM service using local fallback');
  }

  /**
   * Refine raw predicted words into a proper sentence.
   */
  async refineSentence(
    words: string[],
    context?: string
  ): Promise<RefinementResult> {
    if (this.backendAvailable) {
      return this.callBackend(words, context);
    }
    return this.localRefine(words);
  }

  /**
   * Call the backend /api/refine endpoint.
   */
  private async callBackend(
    words: string[],
    context?: string
  ): Promise<RefinementResult> {
    try {
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          words,
          context: context || '',
          session_id: 'frontend',
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();
      return {
        originalText: data.original,
        refinedText: data.refined,
        isComplete: this.isCompleteSentence(data.refined),
      };
    } catch (error) {
      console.error('Backend refinement error:', error);
      // Fallback to local refinement
      return this.localRefine(words);
    }
  }

  /**
   * Local fallback refinement when backend is unavailable.
   */
  private async localRefine(words: string[]): Promise<RefinementResult> {
    // Small delay to simulate processing
    await new Promise((resolve) => setTimeout(resolve, 100));

    const deduped = this.removeConsecutiveDuplicates(words);
    let refined = deduped.join(' ');

    // Capitalise first letter
    refined = refined.charAt(0).toUpperCase() + refined.slice(1).toLowerCase();

    // Add period if not present
    if (!/[.!?]$/.test(refined)) {
      refined += '.';
    }

    refined = this.applyCommonRefinements(refined);

    return {
      originalText: words.join(' '),
      refinedText: refined,
      isComplete: this.isCompleteSentence(refined),
    };
  }

  /**
   * Remove consecutive duplicate words.
   */
  private removeConsecutiveDuplicates(words: string[]): string[] {
    return words.filter((word, index) => {
      if (index === 0) return true;
      return word.toLowerCase() !== words[index - 1].toLowerCase();
    });
  }

  /**
   * Apply common sign language refinements.
   */
  private applyCommonRefinements(text: string): string {
    const refinements: Record<string, string> = {
      'i am': 'I am',
      i: 'I',
      dont: "don't",
      cant: "can't",
      wont: "won't",
      im: "I'm",
      youre: "you're",
      thats: "that's",
      whats: "what's",
      its: "it's",
    };

    let refined = text;
    for (const [key, value] of Object.entries(refinements)) {
      const regex = new RegExp(`\\b${key}\\b`, 'gi');
      refined = refined.replace(regex, value);
    }
    return refined;
  }

  /**
   * Check if the sentence seems complete.
   */
  private isCompleteSentence(text: string): boolean {
    return /[.!?]$/.test(text.trim());
  }

  /**
   * Check if the backend is available.
   */
  isBackendAvailable(): boolean {
    return this.backendAvailable;
  }

  /**
   * Check if running in local fallback mode.
   */
  isMockMode(): boolean {
    return !this.backendAvailable;
  }
}

// Export singleton instance
export const llmService = new LLMService();
export default llmService;
