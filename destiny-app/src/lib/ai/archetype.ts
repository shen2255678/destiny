/**
 * Archetype generator — deterministic version based on RPV values.
 * TODO: Replace with Claude API call for dynamic AI-generated archetypes.
 */

interface UserData {
  rpv_conflict?: string
  rpv_power?: string
  rpv_energy?: string
  sun_sign?: string
  moon_sign?: string
}

interface ArchetypeResult {
  archetype_name: string
  archetype_desc: string
  tags: string[]
  stats: { key: string; label: string; english: string; level: number; max: number; color: string }[]
}

const archetypeMap: Record<string, { name: string; desc: string; tags: string[] }> = {
  'cold_war-control-home': {
    name: 'The Sentinel',
    desc: '你是內心世界的守護者，用沉穩與智慧掌控一切。在關係中，你渴望秩序與深度，用沉默的陪伴表達忠誠。',
    tags: ['守護者', '內斂型', '掌控者', '深思熟慮'],
  },
  'cold_war-control-out': {
    name: 'The Strategist',
    desc: '你是冷靜的策略家，在紛擾中保持清醒。你喜歡掌控局面但不失探索精神，是關係中的穩定錨點。',
    tags: ['策略家', '冷靜型', '探索者', '領導力'],
  },
  'cold_war-follow-home': {
    name: 'The Dreamer',
    desc: '你是安靜的夢想家，在自己的世界裡找到力量。在關係中你渴望被理解和被帶領，用溫柔回應一切。',
    tags: ['夢想家', '溫柔型', '內省', '隨和'],
  },
  'cold_war-follow-out': {
    name: 'The Wanderer',
    desc: '你是不斷追尋深度的靈魂。在關係中，你渴望被真正看見，用陪伴表達忠誠。當你找到真正的共鳴，忠誠超越一切。',
    tags: ['流浪者', '深度追尋者', '忠誠', '獨立'],
  },
  'argue-control-home': {
    name: 'The Guardian',
    desc: '你是直率的守護者，用行動和言語捍衛所愛。在關係中你是決策者，同時渴望溫暖的歸屬感。',
    tags: ['守護者', '直率型', '行動派', '溫暖'],
  },
  'argue-control-out': {
    name: 'The Commander',
    desc: '你是天生的領袖，熱情而果斷。在關係中你喜歡帶領對方探索世界，直面衝突是你的勇氣。',
    tags: ['指揮官', '熱情型', '果斷', '冒險'],
  },
  'argue-follow-home': {
    name: 'The Healer',
    desc: '你是情感的療癒者，直接表達但內心柔軟。在關係中你享受被帶領，用真誠的溝通化解一切。',
    tags: ['療癒者', '真誠型', '柔軟', '共情'],
  },
  'argue-follow-out': {
    name: 'The Explorer',
    desc: '你是自由的探險家，熱愛溝通與新體驗。在關係中你享受被帶領去未知的旅程，直覺是你的羅盤。',
    tags: ['探險家', '自由型', '直覺', '熱情'],
  },
}

const defaultArchetype = {
  name: 'The Seeker',
  desc: '你是永恆的追尋者，在關係中尋找靈魂的共鳴。你的獨特性正在被解碼，等待命運的揭示。',
  tags: ['追尋者', '獨特', '靈魂共鳴', '神秘'],
}

export function generateArchetype(userData: UserData): ArchetypeResult {
  const key = `${userData.rpv_conflict || 'cold_war'}-${userData.rpv_power || 'follow'}-${userData.rpv_energy || 'home'}`
  const match = archetypeMap[key] || defaultArchetype

  // Deterministic stats based on RPV values
  const passion = userData.rpv_conflict === 'argue' ? 8 : 5
  const stability = userData.rpv_energy === 'home' ? 8 : 5
  const intellect = userData.rpv_power === 'control' ? 8 : 6

  return {
    archetype_name: match.name,
    archetype_desc: match.desc,
    tags: match.tags,
    stats: [
      { key: 'passion', label: '激情', english: 'Passion', level: passion, max: 10, color: '#d98695' },
      { key: 'stability', label: '穩定', english: 'Stability', level: stability, max: 10, color: '#a8e6cf' },
      { key: 'intellect', label: '智識', english: 'Intellect', level: intellect, max: 10, color: '#f7c5a8' },
    ],
  }
}
