export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type AccuracyType = 'PRECISE' | 'TWO_HOUR_SLOT' | 'FUZZY_DAY'

export type RectificationStatus =
  | 'unrectified'
  | 'collecting_signals'
  | 'narrowed_to_2hr'
  | 'narrowed_to_d9'
  | 'locked'
  | 'needs_review'

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          display_name: string | null
          gender: 'male' | 'female' | 'non-binary'
          birth_date: string
          birth_time: 'precise' | 'morning' | 'afternoon' | 'evening' | 'unknown' | null
          birth_time_exact: string | null
          birth_city: string
          birth_lat: number | null
          birth_lng: number | null
          data_tier: number
          rpv_conflict: 'cold_war' | 'argue' | null
          rpv_power: 'control' | 'follow' | null
          rpv_energy: 'home' | 'out' | null
          sun_sign: string | null
          moon_sign: string | null
          venus_sign: string | null
          mars_sign: string | null
          saturn_sign: string | null
          ascendant_sign: string | null
          mercury_sign: string | null
          jupiter_sign: string | null
          pluto_sign: string | null
          chiron_sign: string | null
          juno_sign: string | null
          house4_sign: string | null
          house8_sign: string | null
          attachment_style: 'anxious' | 'avoidant' | 'secure' | 'disorganized' | null
          attachment_role: 'dom_secure' | 'sub_secure' | 'balanced' | null
          power_dynamic: 'dominant' | 'submissive' | 'switch' | null
          energy_level: number | null
          element_primary: 'fire' | 'earth' | 'air' | 'water' | null
          archetype_name: string | null
          archetype_desc: string | null
          bio: string | null
          interest_tags: Json
          social_energy: 'high' | 'medium' | 'low'
          bazi_day_master: string | null
          bazi_element: 'wood' | 'fire' | 'earth' | 'metal' | 'water' | null
          bazi_four_pillars: Json | null
          onboarding_step: 'birth_data' | 'rpv_test' | 'photos' | 'soul_report' | 'complete'
          // Rectification fields
          accuracy_type: AccuracyType | null
          window_start: string | null
          window_end: string | null
          window_size_minutes: number | null
          rectification_status: RectificationStatus
          current_confidence: number
          active_range_start: string | null
          active_range_end: string | null
          calibrated_time: string | null
          active_d9_slot: number | null
          is_boundary_case: boolean
          dealbreakers: string[]
          priorities: 'Achievement' | 'LifeQuality' | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          display_name?: string | null
          gender: 'male' | 'female' | 'non-binary'
          birth_date: string
          birth_time?: 'precise' | 'morning' | 'afternoon' | 'evening' | 'unknown' | null
          birth_time_exact?: string | null
          birth_city: string
          birth_lat?: number | null
          birth_lng?: number | null
          data_tier?: number
          rpv_conflict?: 'cold_war' | 'argue' | null
          rpv_power?: 'control' | 'follow' | null
          rpv_energy?: 'home' | 'out' | null
          sun_sign?: string | null
          moon_sign?: string | null
          venus_sign?: string | null
          mars_sign?: string | null
          saturn_sign?: string | null
          ascendant_sign?: string | null
          mercury_sign?: string | null
          jupiter_sign?: string | null
          pluto_sign?: string | null
          chiron_sign?: string | null
          juno_sign?: string | null
          house4_sign?: string | null
          house8_sign?: string | null
          attachment_style?: 'anxious' | 'avoidant' | 'secure' | 'disorganized' | null
          attachment_role?: 'dom_secure' | 'sub_secure' | 'balanced' | null
          power_dynamic?: 'dominant' | 'submissive' | 'switch' | null
          energy_level?: number | null
          element_primary?: 'fire' | 'earth' | 'air' | 'water' | null
          archetype_name?: string | null
          archetype_desc?: string | null
          bio?: string | null
          interest_tags?: Json
          social_energy?: 'high' | 'medium' | 'low'
          bazi_day_master?: string | null
          bazi_element?: 'wood' | 'fire' | 'earth' | 'metal' | 'water' | null
          bazi_four_pillars?: Json | null
          onboarding_step?: 'birth_data' | 'rpv_test' | 'photos' | 'soul_report' | 'complete'
          // Rectification fields
          accuracy_type?: AccuracyType | null
          window_start?: string | null
          window_end?: string | null
          window_size_minutes?: number | null
          rectification_status?: RectificationStatus
          current_confidence?: number
          active_range_start?: string | null
          active_range_end?: string | null
          calibrated_time?: string | null
          active_d9_slot?: number | null
          is_boundary_case?: boolean
          dealbreakers?: string[]
          priorities?: 'Achievement' | 'LifeQuality' | null
        }
        Update: Partial<Database['public']['Tables']['users']['Insert']>
        Relationships: []
      }
      photos: {
        Row: {
          id: string
          user_id: string
          storage_path: string
          blurred_path: string
          half_blurred_path: string | null
          upload_order: number
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          storage_path: string
          blurred_path: string
          half_blurred_path?: string | null
          upload_order: number
        }
        Update: Partial<Database['public']['Tables']['photos']['Insert']>
        Relationships: [
          {
            foreignKeyName: 'photos_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          }
        ]
      }
      daily_matches: {
        Row: {
          id: string
          user_id: string
          matched_user_id: string
          match_date: string
          kernel_score: number | null
          power_score: number | null
          glitch_score: number | null
          total_score: number | null
          match_type: 'complementary' | 'similar' | 'tension' | null
          tags: Json
          radar_passion: number | null
          radar_stability: number | null
          radar_communication: number | null
          card_color: 'coral' | 'blue' | 'purple' | null
          user_action: 'pending' | 'accept' | 'pass'
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          matched_user_id: string
          match_date?: string
          kernel_score?: number | null
          power_score?: number | null
          glitch_score?: number | null
          total_score?: number | null
          match_type?: 'complementary' | 'similar' | 'tension' | null
          tags?: Json
          radar_passion?: number | null
          radar_stability?: number | null
          radar_communication?: number | null
          card_color?: 'coral' | 'blue' | 'purple' | null
          user_action?: 'pending' | 'accept' | 'pass'
        }
        Update: Partial<Database['public']['Tables']['daily_matches']['Insert']>
        Relationships: [
          {
            foreignKeyName: 'daily_matches_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          },
          {
            foreignKeyName: 'daily_matches_matched_user_id_fkey'
            columns: ['matched_user_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          }
        ]
      }
      connections: {
        Row: {
          id: string
          user_a_id: string
          user_b_id: string
          match_id: string | null
          icebreaker_question: string | null
          user_a_answer: string | null
          user_b_answer: string | null
          icebreaker_tags: Json | null
          sync_level: number
          message_count: number
          call_duration: number
          status: 'icebreaker' | 'active' | 'expired'
          last_activity: string
          created_at: string
        }
        Insert: {
          id?: string
          user_a_id: string
          user_b_id: string
          match_id?: string | null
          icebreaker_question?: string | null
          user_a_answer?: string | null
          user_b_answer?: string | null
          icebreaker_tags?: Json | null
          sync_level?: number
          message_count?: number
          call_duration?: number
          status?: 'icebreaker' | 'active' | 'expired'
        }
        Update: Partial<Database['public']['Tables']['connections']['Insert']>
        Relationships: [
          {
            foreignKeyName: 'connections_user_a_id_fkey'
            columns: ['user_a_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          },
          {
            foreignKeyName: 'connections_user_b_id_fkey'
            columns: ['user_b_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          }
        ]
      }
      messages: {
        Row: {
          id: string
          connection_id: string
          sender_id: string
          content: string
          created_at: string
        }
        Insert: {
          id?: string
          connection_id: string
          sender_id: string
          content: string
        }
        Update: Partial<Database['public']['Tables']['messages']['Insert']>
        Relationships: [
          {
            foreignKeyName: 'messages_connection_id_fkey'
            columns: ['connection_id']
            referencedRelation: 'connections'
            referencedColumns: ['id']
          },
          {
            foreignKeyName: 'messages_sender_id_fkey'
            columns: ['sender_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          }
        ]
      }
      rectification_events: {
        Row: {
          id: string
          user_id: string
          ts: string
          source: 'signup' | 'daily_quiz' | 'interaction' | 'post_date_feedback' | 'admin'
          event_type: 'range_initialized' | 'range_narrowed' | 'candidate_eliminated' | 'confidence_updated' | 'locked' | 'flagged_needs_review'
          payload: Json
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          ts?: string
          source: 'signup' | 'daily_quiz' | 'interaction' | 'post_date_feedback' | 'admin'
          event_type: 'range_initialized' | 'range_narrowed' | 'candidate_eliminated' | 'confidence_updated' | 'locked' | 'flagged_needs_review'
          payload?: Json
        }
        Update: Partial<Database['public']['Tables']['rectification_events']['Insert']>
        Relationships: [
          {
            foreignKeyName: 'rectification_events_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          }
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
  }
}
