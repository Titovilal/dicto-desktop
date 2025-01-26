<script setup>
import AudioRecorder from './components/AudioRecorder.vue'
</script>

<template>
  <div class="min-h-screen bg-white">
    <div class="max-w-3xl mx-auto px-6 py-12">
      <header class="text-center mb-12">
        <h1 class="text-4xl font-bold text-gray-900">Dicto</h1>
        <p class="mt-3 text-lg text-gray-500">Instantly convert your voice to text</p>
      </header>
      <main>
        <AudioRecorder />
      </main>
    </div>
  </div>
</template>
