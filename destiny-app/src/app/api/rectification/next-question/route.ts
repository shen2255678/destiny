import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

// ---------------------------------------------------------------------------
// Question bank (Via Negativa — MVP set)
// ---------------------------------------------------------------------------

interface QuestionOption {
  id: 'A' | 'B'
  label: string
  eliminates: string[]
}

interface Question {
  question_id: string
  phase: 'coarse' | 'fine'
  question_text: string
  options: QuestionOption[]
}

const QUESTION_BANK: Question[] = [
  {
    question_id: 'ascendant_exclusion_fire_earth',
    phase: 'fine',
    question_text: '在過往的人生中，別人對你的第一印象，哪一個是「絕對不可能」發生的？',
    options: [
      {
        id: 'A',
        label: '被認為是「過度熱情、講話很大聲、停不下來」的人',
        eliminates: ['ascendant_sagittarius', 'ascendant_leo', 'ascendant_aries'],
      },
      {
        id: 'B',
        label: '被認為是「反應很慢、太過嚴肅、存在感很低」的人',
        eliminates: ['ascendant_capricorn', 'ascendant_taurus', 'ascendant_scorpio'],
      },
    ],
  },
  {
    question_id: 'moon_exclusion_aries_taurus',
    phase: 'coarse',
    question_text: '如果必須選一種，下面哪種情況會讓你更想原地爆炸？',
    options: [
      {
        id: 'A',
        label: '動作慢吞吞，想做什麼都要層層審核，完全沒有自主權',
        eliminates: ['moon_aries', 'moon_fire_signs', 'moon_cardinal'],
      },
      {
        id: 'B',
        label: '事情完全失控，計畫改了又改，還要面對突發狀況',
        eliminates: ['moon_taurus', 'moon_earth_signs', 'moon_fixed'],
      },
    ],
  },
  {
    question_id: 'bazi_social_battery',
    phase: 'coarse',
    question_text: '放假時被拉去參加一個 10 人的陌生聚會，你的內心 OS 是？',
    options: [
      {
        id: 'A',
        label: '好耶！正好可以認識新朋友，展現我的魅力',
        eliminates: ['bazi_weak_daymaster'],
      },
      {
        id: 'B',
        label: '天啊饒了我吧，我只想要一個人靜靜或跟熟人待著',
        eliminates: ['bazi_strong_daymaster'],
      },
    ],
  },
  {
    question_id: 'bazi_crisis_reaction',
    phase: 'fine',
    question_text: '工作遇到極不合理的笨蛋需求，你最「做不到」的反應是？',
    options: [
      {
        id: 'A',
        label: '為了皇城內的和氣，雖然不爽但還是笑笑地吞下去照做',
        eliminates: ['bazi_hour_guan_yin', 'bazi_official_seal'],
      },
      {
        id: 'B',
        label: '直接拍桌翻臉，或者冷嘲熱諷對方一頓然後拒做',
        eliminates: ['bazi_hour_shishang_qisha', 'bazi_output_power'],
      },
    ],
  },
]

// ---------------------------------------------------------------------------
// Route handler
// ---------------------------------------------------------------------------

export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const { data: userData } = await supabase
    .from('users')
    .select('accuracy_type, rectification_status, current_confidence, window_size_minutes, is_boundary_case')
    .eq('id', user.id)
    .single()

  if (!userData) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 })
  }

  // No rectification needed: PRECISE or already locked
  if (
    userData.accuracy_type === 'PRECISE' ||
    userData.rectification_status === 'locked' ||
    (userData.current_confidence ?? 0) >= 0.8
  ) {
    return new NextResponse(null, { status: 204 })
  }

  // Select question based on boundary case priority (spec §GET next-question)
  let question: Question

  if (userData.is_boundary_case) {
    // Ascendant boundary case → highest priority fine question
    question = QUESTION_BANK.find(q => q.question_id.includes('ascendant')) ?? QUESTION_BANK[1]
  } else if ((userData.window_size_minutes ?? 0) >= 360) {
    // Large window → coarse filter first
    question = QUESTION_BANK.find(q => q.phase === 'coarse') ?? QUESTION_BANK[1]
  } else {
    // Narrowed window → fine filter
    question = QUESTION_BANK.find(q => q.phase === 'fine') ?? QUESTION_BANK[0]
  }

  return NextResponse.json({
    ...question,
    context: {
      current_confidence: userData.current_confidence ?? 0,
      rectification_status: userData.rectification_status,
      is_boundary_case: userData.is_boundary_case ?? false,
    },
  })
}
