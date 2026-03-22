<template>
  <section class="page">
    <div class="card" style="max-width: 420px; margin: 48px auto;">
      <h1 class="page-title">Login</h1>
      <p class="muted">Development login placeholder.</p>

      <form @submit.prevent="handleLogin" style="display: grid; gap: 12px; margin-top: 16px;">
        <input v-model="email" type="email" placeholder="Email" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit">Sign in</button>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const email = ref("admin@example.com");
const password = ref("admin");
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

function handleLogin(): void {
  authStore.login(email.value, "dev-token");
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
  void router.push(redirect);
}
</script>
