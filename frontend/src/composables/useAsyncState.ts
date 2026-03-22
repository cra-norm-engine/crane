import { ref } from "vue";

export function useAsyncState() {
  const isLoading = ref(false);
  const errorMessage = ref("");

  async function execute<T>(task: () => Promise<T>): Promise<T> {
    isLoading.value = true;
    errorMessage.value = "";
    try {
      return await task();
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "Unknown error";
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    isLoading,
    errorMessage,
    execute,
  };
}