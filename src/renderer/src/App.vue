<script setup>
import Versions from './components/Versions.vue'
import AudioRecorder from './components/AudioRecorder.vue'

const ipcHandle = () => window.electron.ipcRenderer.send('ping')
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
