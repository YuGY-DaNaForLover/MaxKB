<script setup lang="ts"></script>

<template>
  <img src="@/assets/bg.png" alt="bg" class="bg-img" />
  <router-view />
</template>

<style scoped>
.bg-img {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 400px;
  opacity: 0.5;
}
</style>
