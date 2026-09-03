<template>
  <section class="card related-tasks">
    <div class="related-tasks__head">
      <div><h2>Related tasks</h2><p>{{ openTasks.length }} open · {{ completedTasks.length }} completed</p></div>
      <RouterLink :to="createLink" class="btn btn-primary btn-compact">New task</RouterLink>
    </div>
    <p v-if="loading" class="muted">Loading tasks…</p>
    <p v-else-if="!tasks.length" class="muted">No tasks are linked here yet.</p>
    <template v-else>
      <div v-if="openTasks.length" class="related-group"><h3>Open</h3>
        <button v-for="task in openTasks.slice(0, 8)" :key="task.entity_id" class="related-task" @click="selectedTask = task">
          <span class="related-task__title">{{ task.title }}</span>
          <span>{{ task.priority }} · {{ task.assigned_to_name || "Unassigned" }} · {{ task.due_date || "No due date" }}</span>
        </button>
      </div>
      <div v-if="completedTasks.length" class="related-group"><h3>Completed</h3>
        <button v-for="task in completedTasks.slice(0, 8)" :key="task.entity_id" class="related-task" @click="selectedTask = task">
          <span class="related-task__title">{{ task.title }}</span>
          <span>{{ task.assigned_to_name || "Unassigned" }} · completed</span>
        </button>
      </div>
    </template>
    <RouterLink v-if="tasks.length > 8" :to="listLink" class="related-tasks__more">View all {{ tasks.length }} tasks</RouterLink>
  </section>
  <TaskDrawer :task="selectedTask" @close="selectedTask = null" @edit="openInWorkspace" @navigate="openInWorkspace" @task-updated="onTaskUpdated" @status-updated="load" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import TaskDrawer from "@/components/TaskDrawer.vue";
import { taskService } from "@/services/task-service";
import type { TaskItem } from "@/types/task";

const props = defineProps<{ productId: string; releaseId?: string | null }>();
const router = useRouter();
const tasks = ref<TaskItem[]>([]);
const selectedTask = ref<TaskItem | null>(null);
const loading = ref(false);
const query = computed(() => ({ product: props.productId, ...(props.releaseId ? { release: props.releaseId } : {}) }));
const createLink = computed(() => ({ name: "my-tasks", query: { ...query.value, new: "1" } }));
const listLink = computed(() => ({ name: "my-tasks", query: query.value }));
const openTasks = computed(() => tasks.value.filter((task) => !task.is_completed && !task.archived_at));
const completedTasks = computed(() => tasks.value.filter((task) => task.is_completed && !task.archived_at));

async function load(): Promise<void> {
  loading.value = true;
  try {
    tasks.value = (await taskService.listMyTasks(true, { scope: "all", state: "all", product_id: props.productId, ...(props.releaseId ? { product_release_id: props.releaseId } : {}) })).filter((task) => !task.archived_at);
  } finally { loading.value = false; }
}

function onTaskUpdated(updated: TaskItem): void {
  const index = tasks.value.findIndex((task) => task.entity_id === updated.entity_id);
  if (index >= 0) tasks.value[index] = updated;
  selectedTask.value = updated;
}

function openInWorkspace(task: TaskItem): void {
  void router.push({ name: "my-tasks", query: { task: task.entity_id } });
}

onMounted(load);
watch(() => [props.productId, props.releaseId], load);
</script>

<style scoped>
.related-tasks { padding: 1rem; }
.related-tasks__head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: .75rem; }
.related-tasks__head h2 { margin: 0; font-size: 1rem; }
.related-tasks__head p { margin: .2rem 0 0; color: var(--color-text-muted); font-size: .8rem; }
.related-group h3 { margin: .8rem 0 .25rem; color: var(--color-text-muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .05em; }
.related-task { width: 100%; display: flex; justify-content: space-between; gap: 1rem; padding: .65rem 0; border: 0; border-top: 1px solid var(--color-border); background: transparent; color: var(--color-text-muted); cursor: pointer; text-align: left; font-size: .78rem; }
.related-task:hover .related-task__title { color: var(--color-primary); }
.related-task__title { color: var(--color-text); font-weight: 600; }
.related-tasks__more { display: inline-block; margin-top: .65rem; font-size: .8rem; }
</style>
