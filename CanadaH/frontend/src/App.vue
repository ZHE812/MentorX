<template>
  <div class="min-h-screen bg-[#020617] text-slate-100 font-sans relative overflow-hidden selection:bg-cyan-500/30">
    <div class="fixed inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20 pointer-events-none"></div>
    <div class="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none animate-pulse"></div>
    <div class="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none animate-pulse" style="animation-delay: 2s"></div>

    <video ref="video" autoplay playsinline hidden></video>

    <main class="relative z-10 max-w-[1700px] mx-auto px-8 py-10">
      <header class="flex flex-col md:flex-row md:items-center justify-between mb-12 gap-8 px-2">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h1 class="text-7xl font-black tracking-tighter bg-gradient-to-br from-white via-cyan-400 to-emerald-500 bg-clip-text text-transparent italic drop-shadow-sm pr-4">
              MENTOR X
            </h1>
            <span class="px-3 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] font-bold tracking-[0.3em] text-slate-500 uppercase">Pro v1.0</span>
          </div>
          <p class="text-slate-400 font-medium tracking-[0.2em] uppercase text-xs flex items-center gap-2">
            <span class="w-12 h-[1px] bg-slate-700"></span>
            {{ t('AI 健身姿勢矯正系統', 'AI-Powered Training Hub') }}
          </p>
        </div>
        
        <div class="flex items-center gap-6">
          <button @click="isEnglish = !isEnglish" 
            class="group relative w-14 h-14 flex items-center justify-center bg-slate-900 border border-slate-700/50 rounded-2xl hover:border-cyan-500/50 transition-all duration-300"
            :title="isEnglish ? 'Switch to Chinese' : 'Switch to English'">
            <svg class="w-7 h-7 text-slate-400 group-hover:text-cyan-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
            <span class="absolute -bottom-6 text-[10px] font-bold tracking-widest text-slate-500 uppercase">{{ isEnglish ? 'EN' : 'ZH' }}</span>
          </button>
          
          <div class="bg-slate-900/80 backdrop-blur-2xl border border-white/5 px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-4">
            <div :class="['w-3 h-3 rounded-full transition-all duration-500 shadow-[0_0_10px]', connectionStatus === 'online' ? 'bg-emerald-400 shadow-emerald-400/50' : 'bg-rose-500 shadow-rose-500/50 animate-pulse']"></div>
            <span class="text-xs font-black tracking-widest uppercase text-slate-300">
              {{ connectionStatus === 'online' ? t('系統在線', 'SYSTEM ONLINE') : t('連線中斷', 'DISCONNECTED') }}
            </span>
          </div>
        </div>
      </header>

      <nav class="flex gap-4 mb-12 overflow-x-auto pb-4 custom-scrollbar px-2 no-scrollbar justify-center">
        <button v-for="mode in exerciseModes" :key="mode.id" 
          @click="selectMode(mode.id)"
          :class="['px-12 py-5 rounded-2xl font-black text-sm whitespace-nowrap transition-all duration-300 border uppercase tracking-[0.2em]', 
          currentMode === mode.id ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 border-white/20 text-white shadow-xl scale-105' : 'bg-white/5 border-white/5 text-slate-500 hover:bg-white/10 hover:text-slate-200']">
          {{ mode.name }}
        </button>
      </nav>

      <div class="w-full">
        <section v-if="!isTraining" class="grid lg:grid-cols-3 gap-10 animate-in fade-in zoom-in-95 duration-700">
          
          <div class="group bg-slate-900/40 backdrop-blur-3xl border border-white/5 p-12 rounded-[3.5rem] shadow-2xl hover:border-cyan-500/30 transition-all duration-500 flex flex-col justify-center">
            <div class="flex items-center gap-4 mb-12 text-2xl font-black text-white uppercase tracking-widest">
              <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center shadow-lg">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
              </div>
              {{ t('個人教練設定', 'AI COACH PROFILE') }}
            </div>
            <div class="space-y-12">
              <div v-for="attr in ['height', 'weight', 'age']" :key="attr" class="space-y-4">
                <label class="text-sm text-slate-500 font-black uppercase tracking-widest px-2 text-center block">{{ t(attr === 'height' ? '身高 CM' : attr === 'weight' ? '體重 KG' : '年齡', attr.toUpperCase()) }}</label>
                <input type="number" v-model="userProfile[attr]" class="w-full bg-black/40 border border-white/10 rounded-[2rem] py-8 text-center text-4xl font-black text-white focus:border-emerald-500 outline-none transition-all focus:shadow-[0_0_20px_rgba(16,185,129,0.2)]">
              </div>
            </div>
          </div>

          <div class="bg-slate-900/40 backdrop-blur-3xl border border-white/5 p-12 rounded-[3.5rem] shadow-2xl hover:border-emerald-500/30 transition-all duration-500 flex flex-col justify-center text-center">
            <div class="flex items-center justify-center gap-4 mb-16 text-2xl font-black text-white uppercase tracking-widest">
              <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center shadow-lg">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              </div>
              {{ t('訓練目標設定', 'TARGET SETTINGS') }}
            </div>
            <div class="space-y-16">
              <div class="space-y-6">
                <span class="text-sm text-slate-400 font-bold uppercase tracking-widest block">{{ t('單組目標次數', 'TARGET REPS') }}</span>
                <input type="number" v-model="targetReps" class="w-full bg-black/40 border border-white/10 rounded-[2rem] py-12 text-center text-7xl font-black text-emerald-400 outline-none focus:border-cyan-500 transition-all">
              </div>
              <div class="space-y-6">
                <span class="text-sm text-slate-400 font-bold uppercase tracking-widest block">{{ t('預計完成組數', 'TARGET SETS') }}</span>
                <input type="number" v-model="targetSets" class="w-full bg-black/40 border border-white/10 rounded-[2rem] py-12 text-center text-7xl font-black text-cyan-400 outline-none focus:border-emerald-500 transition-all">
              </div>
            </div>
          </div>

          <div class="bg-slate-900/40 backdrop-blur-3xl border border-white/5 p-12 rounded-[3.5rem] shadow-2xl group/guide flex flex-col justify-between h-full">
            <div @click="isImageOpen = true" class="w-full aspect-video rounded-[2.5rem] bg-black/40 mb-10 border border-white/10 flex items-center justify-center overflow-hidden relative cursor-zoom-in group/img hover:border-cyan-500/40 transition-all duration-500">
   
            <img :src="`/guides/${currentMode}.png`" class="w-full h-full object-contain p-8 relative z-10 transition-all duration-500 group-hover/img:scale-110 group-hover/img:brightness-50" :alt="currentMode" />
   
            <div class="absolute inset-0 flex items-center justify-center z-20 opacity-0 group-hover/img:opacity-100 transition-opacity duration-500 pointer-events-none">
              <span class="bg-black/60 text-white px-6 py-3 rounded-full text-sm font-bold uppercase tracking-[0.2em] shadow-2xl backdrop-blur-md flex items-center gap-2">
                <svg class="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" /></svg>
                {{ t('點擊放大', 'CLICK TO ZOOM') }}
              </span>
            </div>

            </div>
            <div class="space-y-8 flex-1">
              <h4 class="text-4xl font-black text-white italic tracking-tight">{{ currentGuide.desc }}</h4>
              <div class="p-8 bg-cyan-500/5 rounded-[2.5rem] border border-cyan-500/10 shadow-inner">
                <p class="text-base text-cyan-400 font-medium leading-relaxed">
                  <span class="font-black uppercase text-xs mr-3 opacity-60">Coach Tip</span>
                  {{ currentGuide.tips }}
                </p>
              </div>
            </div>
            <button @click="handleStartClick" class="w-full mt-12 bg-gradient-to-br from-emerald-400 via-emerald-500 to-cyan-500 py-8 rounded-[2rem] font-black uppercase tracking-[0.4em] text-sm text-white hover:shadow-[0_20px_60px_-10px_rgba(16,185,129,0.4)] hover:-translate-y-2 active:translate-y-0 transition-all duration-300">
              {{ t('即刻啟動訓練', 'START MISSION') }}
            </button>
          </div>
        </section>

        <section v-else class="lg:col-span-12 relative animate-in fade-in slide-in-from-bottom-10 duration-1000 ease-in-out">
          <div class="relative bg-[#020617] rounded-[4.5rem] overflow-hidden border border-white/10 shadow-[0_0_100px_-20px_rgba(0,0,0,1)] aspect-video group">
            <canvas ref="canvas" width="640" height="480" class="w-full h-full object-cover scale-x-[-1] brightness-110"></canvas>
            
            <div class="absolute top-12 left-12 flex flex-col gap-10">
              <div class="bg-black/60 backdrop-blur-3xl border border-white/10 p-12 rounded-[4rem] min-w-[350px] shadow-3xl">
                <div class="flex justify-between items-center mb-6">
                  <span class="text-xs font-black text-cyan-400 uppercase tracking-widest">{{ currentMode === 'plank' ? t('計時器', 'TIMER') : t('累計次數', 'REPS COUNT') }}</span>
                  <div class="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-ping"></div>
                </div>
                <div class="flex items-baseline gap-6">
                  <p class="text-[12rem] font-black text-white leading-none drop-shadow-[0_0_50px_rgba(255,255,255,0.25)]">
                    {{ currentMode === 'plank' ? analysis.timer : analysis.count }}
                  </p>
                  <span class="text-slate-500 font-black italic text-3xl ml-2 uppercase">{{ currentMode === 'plank' ? 'SEC' : 'X' }}</span>
                </div>
                <div class="mt-12 flex items-center gap-8">
                   <div class="flex-1 h-4 bg-white/5 rounded-full overflow-hidden shadow-inner">
                     <div class="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500" :style="{ width: `${Math.min((analysis.count / targetReps) * 100, 100)}%` }"></div>
                   </div>
                   <span class="text-sm font-black text-slate-400 uppercase tracking-widest">{{ t('組數', 'SET') }} {{ analysis.sets + 1 }} / {{ targetSets }}</span>
                </div>
              </div>
              
              <Transition name="fade">
                <div v-if="hasActionFeedback" class="bg-gradient-to-r from-emerald-500 to-cyan-500 p-1.5 rounded-[3rem] shadow-3xl max-w-xl">
                  <div class="bg-black/80 backdrop-blur-3xl px-12 py-8 rounded-[2.9rem]">
                    <p class="text-2xl font-black text-white italic tracking-[0.1em] text-center uppercase">
                      {{ translatedActionFeedback }}
                    </p>
                  </div>
                </div>
              </Transition>
            </div>

            <div class="absolute top-12 right-12 flex flex-col items-end gap-6 z-[60]">
              <div class="px-10 py-5 bg-white/5 backdrop-blur-3xl border border-white/10 rounded-[2.5rem] flex items-center gap-6">
                <span class="text-xs font-black text-white uppercase tracking-[0.4em]">{{ translatedSystemStatus }}</span>
              </div>
              <button @click="stopTraining" class="group px-14 py-6 bg-rose-500/20 backdrop-blur-3xl border border-rose-500/50 hover:bg-rose-600 hover:text-white rounded-[2.5rem] text-xs font-black text-rose-500 uppercase tracking-widest transition-all duration-300">
                {{ t('中止任務', 'ABORT MISSION') }}
              </button>
            </div>

            <div v-if="!analysis.side_view" class="absolute inset-0 flex items-center justify-center bg-rose-600/40 backdrop-blur-md z-50">
               <div class="bg-white/10 border border-white/20 px-16 py-10 rounded-[3.5rem] backdrop-blur-xl animate-bounce text-center shadow-3xl">
                 <p class="font-black text-white uppercase italic tracking-[0.5em] text-4xl">{{ t('請轉向側面', 'POSITION SIDEWAYS') }}</p>
                 <p class="text-xs text-white/70 uppercase tracking-widest mt-5">Calibrating biometric precision</p>
               </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <Transition name="fade">
      <div v-if="isCountingDown" class="fixed inset-0 z-[200] flex items-center justify-center bg-[#020617] backdrop-blur-3xl">
        <div class="text-center animate-in zoom-in-50 duration-300">
          <p class="text-cyan-400 font-black text-4xl uppercase tracking-[0.8em] mb-12 animate-pulse">{{ t('準備開始', 'GET READY') }}</p>
          <p class="text-[25rem] font-black text-white leading-none italic drop-shadow-[0_0_100px_rgba(34,211,238,0.6)]">
            {{ countdown }}
          </p>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showSummary" class="fixed inset-0 z-[110] flex items-center justify-center bg-[#020617]/98 backdrop-blur-3xl p-6 overflow-y-auto no-scrollbar">
        <div class="bg-slate-950 border border-white/5 w-full max-w-6xl rounded-[4rem] p-12 md:p-20 shadow-3xl relative my-auto animate-in zoom-in-95 duration-500">
          <header class="flex justify-between items-start mb-16">
            <div class="space-y-2">
              <h2 class="text-5xl font-black italic text-white uppercase tracking-tighter">{{ t('訓練任務完成', 'MISSION COMPLETE') }}</h2>
              <p class="text-xs text-slate-500 font-bold uppercase tracking-[0.4em]">{{ t('訓練表現數據結算', 'TRAINING SUMMARY') }}</p>
            </div>
            <div class="text-right">
              <p class="text-6xl font-black text-cyan-500 italic">{{ Math.round(sessionData.totalReps * 0.45) }}</p>
              <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">{{ t('消耗熱量估計', 'ESTIMATED KCAL') }}</p>
            </div>
          </header>
          
          <div class="grid lg:grid-cols-3 gap-16">
            <div class="lg:col-span-1 space-y-8">
              <div class="bg-white/5 p-10 rounded-[3.5rem] border border-white/5">
                <p class="text-xs text-slate-500 uppercase font-black mb-4 tracking-widest">{{ t('總計次數', 'TOTAL REPS') }}</p>
                <p class="text-8xl font-black text-white tracking-tighter">{{ sessionData.totalReps }}<span class="text-2xl text-slate-600 ml-2 italic">x</span></p>
              </div>
              <div class="bg-white/5 p-10 rounded-[3.5rem] border border-white/5">
                <p class="text-xs text-slate-500 uppercase font-black mb-4 tracking-widest">{{ t('姿勢異常偵測', 'POSTURE ERRORS') }}</p>
                <p class="text-8xl font-black text-rose-500 tracking-tighter">{{ sessionData.errorCount }}<span class="text-2xl text-slate-600 ml-2 italic">!</span></p>
              </div>
            </div>

            <div class="lg:col-span-2 bg-white/[0.02] border border-white/5 rounded-[4rem] p-12 relative group/ai">
              <div class="flex items-center gap-6 mb-10">
                <div class="w-16 h-16 rounded-3xl bg-cyan-500 flex items-center justify-center text-white font-black italic text-3xl">G</div>
                <div class="space-y-1">
                  <h3 class="text-lg font-black text-white uppercase tracking-widest">{{ t('AI 私人教練建議', 'GEMINI AI FEEDBACK') }}</h3>
                </div>
              </div>
              <div class="min-h-[350px] text-slate-300 text-lg leading-relaxed overflow-y-auto custom-scrollbar pr-6">
                <div v-if="aiLoading" class="flex flex-col items-center justify-center py-24 gap-8">
                  <div class="flex gap-3"><div v-for="i in 3" :key="i" class="w-3 h-3 bg-cyan-500 rounded-full animate-bounce" :style="{animationDelay: `${i*0.2}s`}"></div></div>
                  <p class="text-xs text-cyan-400 tracking-[0.5em] font-black uppercase">{{ t('正在解析數據...', 'ANALYZING...') }}</p>
                </div>
                <div v-else-if="aiAdvice" class="whitespace-pre-wrap font-medium">{{ aiAdvice }}</div>
                <div v-else class="flex flex-col items-center justify-center py-24 text-slate-600 italic text-center">
                  <p class="text-sm uppercase tracking-widest">{{ t('完成訓練後將顯示建議', 'No feedback available') }}</p>
                </div>
              </div>
            </div>
          </div>
          <button @click="showSummary = false" class="w-full mt-20 bg-white text-black py-8 rounded-[2.5rem] font-black uppercase tracking-[0.5em] text-sm hover:bg-cyan-400 transition-all duration-300 shadow-3xl">
            {{ t('同步數據並返回基地', 'SYNC & RETURN BASE') }}
          </button>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isImageOpen" @click="isImageOpen = false" class="fixed inset-0 z-[150] flex items-center justify-center bg-black/95 backdrop-blur-3xl p-8 cursor-zoom-out">
        <img :src="`/guides/${currentMode}.png`" class="max-w-6xl max-h-[85vh] object-contain shadow-2xl rounded-[3rem] animate-in zoom-in-95 duration-500" />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';

const video = ref(null);
const canvas = ref(null);
const connectionStatus = ref('offline');
const currentMode = ref('squat');
const targetReps = ref(12);
const targetSets = ref(3);
const isEnglish = ref(true); 
const isTraining = ref(false);
const isImageOpen = ref(false);
const showSummary = ref(false);

const isCountingDown = ref(false);
const countdown = ref(3);

const userProfile = ref({ height: 175, weight: 70, age: 25 });
const aiAdvice = ref('');
const aiLoading = ref(false);

const t = (zh, en) => isEnglish.value ? en : zh;
const analysis = ref({ angle: 0, status: 'Waiting...', count: 0, sets: 0, timer: 0, side_view: true, error_type: null });
const sessionData = ref({ startTime: 0, totalReps: 0, errorCount: 0, logs: [], repHistory: [] });

let socket = null;
let intervalId = null;

// --- WebSocket 強化連線邏輯 ---
const initWebSocket = () => {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
  
  socket = new WebSocket('ws://127.0.0.1:8000/ws/pose');
  
  socket.onopen = () => { 
    connectionStatus.value = 'online'; 
  };
  
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      Object.assign(analysis.value, data);
      
      // 只有當 isTraining 為真且 canvas 已經渲染出來時才繪製
      if (isTraining.value && canvas.value && video.value) {
        const ctx = canvas.value.getContext('2d');
        ctx.clearRect(0, 0, 640, 480);
        ctx.drawImage(video.value, 0, 0, 640, 480);
        if (data.landmarks) drawSkeleton(data.landmarks);
      }
    } catch (e) {
      console.error(e);
    }
  };
  
  socket.onclose = () => {
    connectionStatus.value = 'offline';
    setTimeout(initWebSocket, 3000); // 斷線後 3 秒自動嘗試重連
  };

  socket.onerror = () => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  };
};

// --- 按需傳輸影像邏輯 ---
const startSendingFrames = () => {
  if (intervalId) clearInterval(intervalId);
  
  intervalId = setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN && isTraining.value && video.value) {
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = 640;
      tempCanvas.height = 480;
      const ctx = tempCanvas.getContext('2d');
      ctx.drawImage(video.value, 0, 0, 640, 480);
      
      const frameData = {
        image: tempCanvas.toDataURL('image/jpeg', 0.5).split(',')[1],
        mode: currentMode.value,
        target_reps: targetReps.value
      };
      socket.send(JSON.stringify(frameData));
    }
  }, 130);
};

// --- 啟動訓練與倒數 ---
const handleStartClick = () => {
  isCountingDown.value = true;
  countdown.value = 3;
  
  const timer = setInterval(() => {
    countdown.value--;
    if (countdown.value === 0) {
      clearInterval(timer);
      isCountingDown.value = false;
      isTraining.value = true;
      
      // 等待 Vue 將 v-else 區塊的 canvas 渲染出來後，再啟動傳輸
      nextTick(() => {
        sessionData.value = { startTime: Date.now(), totalReps: 0, errorCount: 0, logs: [], repHistory: [] };
        startSendingFrames();
      });
    }
  }, 1000);
};

const stopTraining = () => {
  isTraining.value = false;
  clearInterval(intervalId);
  showSummary.value = true;
  getGeminiAdvice();
};

const selectMode = (modeId) => {
  currentMode.value = modeId;
  isTraining.value = false;
  clearInterval(intervalId);
};

// --- AI 建議邏輯 ---
const getGeminiAdvice = async () => {
  aiLoading.value = true;
  aiAdvice.value = '';
  try {
    const response = await fetch('http://127.0.0.1:8000/session/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exercise: currentMode.value,
        rep_count: sessionData.value.totalReps,
        error_count: sessionData.value.errorCount,
        rep_history: sessionData.value.repHistory,
        logs: sessionData.value.logs.slice(0, 15),
        user_profile: userProfile.value,
        // ✅ 新增：告訴後端目前需要的語言
        language: isEnglish.value ? 'English' : 'Traditional Chinese'
      })
    });
    const data = await response.json();
    aiAdvice.value = data.feedback;
  } catch (error) {
    aiAdvice.value = t("AI 服務暫不可用。", "AI Service temporarily unavailable.");
  } finally {
    aiLoading.value = false;
  }
};

// --- Watchers ---
watch(() => analysis.value.count, (newVal, oldVal) => {
  if (isTraining.value && newVal > oldVal && newVal > 0) {
    addLog('REP', t(`完成一次動作`, `Completed Rep`));
    sessionData.value.totalReps++;
    if (analysis.value.last_rep) sessionData.value.repHistory.push(analysis.value.last_rep);
  }
});

watch(() => analysis.value.error_type, (newVal) => {
  if (isTraining.value && newVal) {
    const lastLog = sessionData.value.logs[0];
    if (!lastLog || lastLog.message !== analysis.value.status) {
      addLog('ERROR', analysis.value.status);
      sessionData.value.errorCount++;
    }
  }
});

const addLog = (type, message) => {
  const elapsed = Math.round((Date.now() - sessionData.value.startTime) / 1000);
  sessionData.value.logs.unshift({ time: elapsed, type, message });
};

// --- 靜態內容 ---
const currentGuide = computed(() => {
  const guides = {
    squat: { desc: t('深蹲：強化下肢核心', 'Squat: Lower Body Power'), tips: t('重心在足跟，膝蓋不內扣。', 'Heels down, knees out.') },
    pushup: { desc: t('伏地挺身：上肢推力訓練', 'Pushup: Upper Body Strength'), tips: t('背部挺直，手肘成45度。', 'Keep back straight, elbows 45°.') },
    plank: { desc: t('棒式：全身靜態核心', 'Plank: Full Core Stability'), tips: t('屁股不抬高，核心持續發力。', 'Keep hips level, engage core.') },
    bicep_curl: { desc: t('二頭肌彎舉：手臂塑形', 'Bicep Curl: Arm Definition'), tips: t('手肘固定在側，不利用慣性。', 'Elbows fixed, no momentum.') },
    situp: { desc: t('仰臥起坐：腹部肌肉刻劃', 'Situp: Abdominal Sculpting'), tips: t('不拉扯頸部，腹部帶動身體。', 'Avoid neck pulling, use abs.') }
  };
  return guides[currentMode.value];
});

const translatedSystemStatus = computed(() => {
  const s = analysis.value.status;
  if (s.includes("Wait") || s.includes("等待") || s.includes("Ready")) return t("引擎偵測中", "AI MONITORING");
  return t("任務執行中", "MISSION EXECUTING");
});

const translatedActionFeedback = computed(() => {
  const map = { 
    "正在下蹲": t("正在下蹲", "SQUATTING"), "完成一次深蹲！": t("動作完美！", "PERFECT REP"), "請挺直背部！": t("姿勢修正中", "POSTURE ALERT"), 
    "OK": t("保持專注", "KEEP FOCUS"), "Going down": t("正在下降", "GOING DOWN"), "Rep done!": t("次數完成", "REP DONE"),
    "Hold!": t("維持住", "HOLDING"), "Hips too high": t("屁股過高", "HIPS TOO HIGH"), "Arms down": t("手部下放", "ARMS DOWN"),
    "Arms up": t("手部彎舉", "ARMS UP"), "Curl complete!": t("彎舉完成", "CURL DONE"), "Lying flat": t("身體平躺", "LYING FLAT"),
    "Sitting up": t("正在起身", "SITTING UP"), "Rep complete!": t("動作完成", "REP DONE")
  };
  return map[analysis.value.status] || analysis.value.status;
});

const hasActionFeedback = computed(() => !(analysis.value.status.includes("Waiting") || analysis.value.status.includes("等待")));

const exerciseModes = computed(() => [
  { id: 'squat', name: t('深蹲', 'Squat') }, { id: 'pushup', name: t('伏地挺身', 'Pushup') },
  { id: 'plank', name: t('棒式', 'Plank') }, { id: 'bicep_curl', name: t('二頭彎舉', 'Curl') },
  { id: 'situp', name: t('仰臥起坐', 'Situp') }
]);

const drawSkeleton = (landmarks) => {
  if (!canvas.value) return;
  const ctx = canvas.value.getContext('2d');
  const { width, height } = canvas.value;
  ctx.save();
  ctx.strokeStyle = "#10b981"; ctx.lineWidth = 4;
  ctx.shadowBlur = 15; ctx.shadowColor = "#10b981";
  
  const POSE_CONNECTIONS = [[11,12], [11,13], [13,15], [12,14], [14,16], [11,23], [12,24], [23,24], [23,25], [25,27], [24,26], [26,28]];
  POSE_CONNECTIONS.forEach(([i, j]) => {
    const p1 = landmarks[i], p2 = landmarks[j];
    if (p1 && p2 && p1.visibility > 0.5) {
      ctx.beginPath();
      ctx.moveTo(p1.x * width, p1.y * height);
      ctx.lineTo(p2.x * width, p2.y * height);
      ctx.stroke();
    }
  });
  ctx.restore();
};

onMounted(async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    if (video.value) video.value.srcObject = stream;
  } catch (err) {
    console.error("Camera access denied or unavailable.", err);
  }
  initWebSocket();
});

onUnmounted(() => {
  clearInterval(intervalId);
  socket?.close();
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>