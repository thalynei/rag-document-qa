<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Sparkles, Eye, EyeOff, Loader2, User, Mail, Lock,
  FileText, MessageSquare, Shield, ArrowRight
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const isLogin = ref(true)
const loading = ref(false)
const showPassword = ref(false)

const username = ref('')
const email = ref('')
const password = ref('')

const canSubmit = computed(() => {
  if (isLogin.value) {
    return username.value.trim().length > 0 && password.value.length >= 6
  }
  return (
    username.value.trim().length >= 2 &&
    email.value.includes('@') &&
    password.value.length >= 6
  )
})

const passwordStrength = computed(() => {
  const p = password.value
  if (p.length === 0) return { level: 0, label: '', color: '' }
  if (p.length < 6) return { level: 1, label: '太短', color: '#EF4444' }
  if (p.length < 8) return { level: 2, label: '弱', color: '#F59E0B' }
  if (/[A-Z]/.test(p) && /[0-9]/.test(p) && /[^A-Za-z0-9]/.test(p))
    return { level: 4, label: '强', color: '#10B981' }
  return { level: 3, label: '中', color: '#6C63FF' }
})

async function handleSubmit() {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    if (isLogin.value) {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, email.value, password.value)
    }
    router.push('/')
  } catch (e: unknown) {
    toast.show(e instanceof Error ? e.message : '操作失败', 'error')
  } finally {
    loading.value = false
  }
}

function toggleMode() {
  isLogin.value = !isLogin.value
  email.value = ''
}
</script>

<template>
  <div class="login-page">
    <!-- Layer 1: Gradient Background -->
    <div class="bg-layer" />

    <!-- Layer 2: Decorative Blobs -->
    <div class="blob blob-1" />
    <div class="blob blob-2" />
    <div class="blob blob-3" />

    <!-- Main Content -->
    <div class="login-container">
      <!-- Left: Brand (desktop) -->
      <div class="brand-panel">
        <div class="brand-content">
          <div class="brand-logo">
            <div class="logo-icon">
              <Sparkles :size="32" class="text-white" />
            </div>
            <div>
              <h1 class="brand-title">RAG Document QA</h1>
              <p class="brand-subtitle">智能文档问答系统</p>
            </div>
          </div>

          <div class="brand-features">
            <div class="feature-item">
              <div class="feature-icon">
                <FileText :size="22" />
              </div>
              <div>
                <h3>多格式文档支持</h3>
                <p>支持 PDF、DOCX、Markdown、TXT 等主流格式</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <MessageSquare :size="22" />
              </div>
              <div>
                <h3>智能对话问答</h3>
                <p>基于 RAG 技术，精准理解文档内容</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <Shield :size="22" />
              </div>
              <div>
                <h3>对话历史保存</h3>
                <p>所有对话自动保存，随时继续话题</p>
              </div>
            </div>
          </div>

          <p class="brand-quote">"让文档阅读变得简单，让知识获取更加高效"</p>
        </div>
      </div>

      <!-- Right: Form -->
      <div class="form-panel">
        <!-- Layer 3: Glassmorphism Card -->
        <div class="glass-card">
          <!-- Mobile Logo -->
          <div class="mobile-logo">
            <div class="logo-icon-sm">
              <Sparkles :size="28" class="text-white" />
            </div>
            <h1>RAG Document QA</h1>
          </div>

          <h2 class="form-title">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
          <p class="form-subtitle">{{ isLogin ? '登录以继续使用智能问答' : '注册开始您的智能问答之旅' }}</p>

          <form @submit.prevent="handleSubmit" class="login-form">
            <!-- Username -->
            <div class="input-group">
              <label>用户名</label>
              <div class="input-wrapper">
                <User :size="18" class="input-icon" />
                <input
                  v-model="username"
                  type="text"
                  :placeholder="isLogin ? '用户名或邮箱' : '输入用户名'"
                  autocomplete="username"
                />
              </div>
            </div>

            <!-- Email (register) -->
            <Transition name="slide">
              <div v-if="!isLogin" class="input-group">
                <label>邮箱</label>
                <div class="input-wrapper">
                  <Mail :size="18" class="input-icon" />
                  <input
                    v-model="email"
                    type="email"
                    placeholder="your@email.com"
                    autocomplete="email"
                  />
                </div>
              </div>
            </Transition>

            <!-- Password -->
            <div class="input-group">
              <label>密码</label>
              <div class="input-wrapper">
                <Lock :size="18" class="input-icon" />
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="至少 6 位"
                  autocomplete="current-password"
                />
                <button type="button" @click="showPassword = !showPassword" class="eye-btn">
                  <Eye v-if="showPassword" :size="18" />
                  <EyeOff v-else :size="18" />
                </button>
              </div>
              <!-- Password strength -->
              <Transition name="slide">
                <div v-if="!isLogin && password.length > 0" class="strength-bar">
                  <div class="strength-track">
                    <div
                      v-for="i in 4"
                      :key="i"
                      class="strength-segment"
                      :class="{ active: i <= passwordStrength.level }"
                      :style="{ background: i <= passwordStrength.level ? passwordStrength.color : '' }"
                    />
                  </div>
                  <span :style="{ color: passwordStrength.color }">{{ passwordStrength.label }}</span>
                </div>
              </Transition>
            </div>

            <!-- Remember / Forgot -->
            <div v-if="isLogin" class="form-options">
              <label class="checkbox-label">
                <input type="checkbox" />
                <span>记住我</span>
              </label>
              <button type="button" class="link-btn">忘记密码？</button>
            </div>

            <!-- Submit -->
            <button
              type="submit"
              :disabled="!canSubmit || loading"
              class="submit-btn"
              :class="{ enabled: canSubmit && !loading }"
            >
              <Loader2 v-if="loading" :size="20" class="animate-spin" />
              <template v-else>
                <span>{{ isLogin ? '登录' : '注册' }}</span>
                <ArrowRight :size="18" />
              </template>
            </button>
          </form>

          <!-- Divider -->
          <div class="divider">
            <span>或</span>
          </div>

          <!-- Toggle -->
          <p class="toggle-text">
            {{ isLogin ? '没有账号？' : '已有账号？' }}
            <button @click="toggleMode">{{ isLogin ? '立即注册' : '立即登录' }}</button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============================================
   Layer 1: Gradient Background
   ============================================ */
.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.bg-layer {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(108, 99, 255, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(255, 107, 157, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 60% 80%, rgba(16, 163, 127, 0.08) 0%, transparent 50%);
}

/* ============================================
   Layer 2: Decorative Blobs
   ============================================ */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: blob-float 20s ease-in-out infinite;
}

.blob-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 350px;
  height: 350px;
  background: linear-gradient(135deg, #FF6B9D, #F59E0B);
  bottom: -80px;
  right: -80px;
  animation-delay: -7s;
}

.blob-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #10A37F, #6C63FF);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes blob-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(20px, 30px) scale(1.02); }
}

/* ============================================
   Layout
   ============================================ */
.login-container {
  position: relative;
  z-index: 10;
  display: flex;
  min-height: 100vh;
}

/* ============================================
   Left: Brand Panel
   ============================================ */
.brand-panel {
  display: none;
  width: 50%;
  padding: 4rem;
  align-items: center;
  justify-content: center;
}

@media (min-width: 1024px) {
  .brand-panel {
    display: flex;
  }
}

.brand-content {
  max-width: 480px;
  color: white;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.brand-title {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 0.25rem;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-bottom: 3rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.feature-item h3 {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.feature-item p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

.brand-quote {
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

/* ============================================
   Right: Form Panel
   ============================================ */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
}

/* ============================================
   Layer 3: Glassmorphism Card
   ============================================ */
.glass-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  padding: 2.5rem;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  animation: card-enter 0.6s ease-out;
}

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Mobile Logo */
.mobile-logo {
  display: none;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

@media (max-width: 1023px) {
  .mobile-logo {
    display: flex;
  }
}

.logo-icon-sm {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(108, 99, 255, 0.4);
  animation: float 3s ease-in-out infinite;
}

.mobile-logo h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
}

/* Form Title */
.form-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
}

.form-subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 2rem;
}

/* ============================================
   Form Elements
   ============================================ */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.input-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  color: rgba(255, 255, 255, 0.4);
  transition: color 0.2s;
  pointer-events: none;
}

.input-wrapper input {
  width: 100%;
  padding: 0.875rem 1rem 0.875rem 2.75rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s ease;
}

.input-wrapper input::placeholder {
  color: rgba(255, 255, 255, 0.35);
}

.input-wrapper input:focus {
  border-color: #6C63FF;
  background: rgba(108, 99, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2), 0 0 20px rgba(108, 99, 255, 0.1);
}

.input-wrapper input:focus ~ .input-icon,
.input-wrapper:focus-within .input-icon {
  color: #6C63FF;
}

.eye-btn {
  position: absolute;
  right: 0.75rem;
  padding: 0.25rem;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: color 0.2s;
}

.eye-btn:hover {
  color: rgba(255, 255, 255, 0.8);
}

/* Password Strength */
.strength-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.strength-track {
  flex: 1;
  display: flex;
  gap: 4px;
}

.strength-segment {
  height: 4px;
  flex: 1;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
}

.strength-bar span {
  font-size: 0.75rem;
  font-weight: 500;
}

/* Form Options */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.checkbox-label input {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  accent-color: #6C63FF;
}

.link-btn {
  background: none;
  border: none;
  font-size: 0.85rem;
  color: #6C63FF;
  cursor: pointer;
  transition: color 0.2s;
}

.link-btn:hover {
  color: #8B85F0;
}

/* Submit Button */
.submit-btn {
  width: 100%;
  padding: 1rem;
  border-radius: 14px;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.4);
}

.submit-btn.enabled {
  background: linear-gradient(135deg, #6C63FF, #FF6B9D);
  color: white;
  box-shadow: 0 4px 20px rgba(108, 99, 255, 0.4);
}

.submit-btn.enabled:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(108, 99, 255, 0.5);
}

.submit-btn.enabled:active {
  transform: translateY(0);
}

/* Shine effect */
.submit-btn.enabled::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.submit-btn.enabled:hover::after {
  transform: translateX(100%);
}

/* Divider */
.divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.divider span {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Toggle */
.toggle-text {
  text-align: center;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

.toggle-text button {
  background: none;
  border: none;
  color: #6C63FF;
  font-weight: 600;
  cursor: pointer;
  margin-left: 0.25rem;
  transition: color 0.2s;
}

.toggle-text button:hover {
  color: #8B85F0;
  text-decoration: underline;
}

/* ============================================
   Transitions
   ============================================ */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
