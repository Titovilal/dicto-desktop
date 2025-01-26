<script setup>
import AudioRecorder from './components/AudioRecorder.vue'
</script>

<template>
  <div class="container">
    <h1>Grabador de Audio</h1>
    <AudioRecorder />
  </div>
</template>

<style>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

h1 {
  color: #2c3e50;
  margin-bottom: 30px;
}
</style>
