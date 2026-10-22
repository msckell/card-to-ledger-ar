// Everything the page shows comes from site.json, written by the pipeline (pipeline/site_data.py).
// No number on the page is typed by hand.
import raw from './data/site.json'

export type Split = { rules: number; ai: number; review: number }

export type QueueItem = {
  id: string
  type: string
  title: string
  next_step: string
  facts: string
  explanation: string
  explanation_source: 'ai_verified' | 'template'
  status: string
  txn?: {
    id: string
    date: string
    type: string
    descriptor: string
    amount: string
    currency: string
    ars: string
    rate: string
    cardholder: string
    memo: string
    proposed_account: string | null
  }
  ai?: { id: string; account: string; confidence: string; reason: string }
  receipt?: { id: string; vendor: string | null; date: string | null; amount: string | null; currency: string | null; file: string }
}

export type ThresholdRow = {
  threshold: string
  accepted: number
  share_auto_accepted: string
  accuracy: string | null
  errors_accepted: number
}

export type Flow = {
  total: number
  by_rule: number
  no_rule: number
  rules_resolved: number
  rules_to_review: number
  ai_resolved: number
  ai_to_review: number
  review_reasons: { type: string; title: string; n: number }[]
}

export type SpendRow = { account: string; name: string; ars: string; ars_compact: string; cents: number; pending: boolean }

export type Example = {
  path: 'rules' | 'ai' | 'review'
  txn: { id: string; date: string; descriptor: string; amount: string; currency: string; rate: string; ars: string }
  receipt: { id: string; vendor: string | null; date: string | null; amount: string | null; currency: string | null; file: string; read_by: string } | null
  coding:
    | { by: 'rule'; id: string; pattern: string; account: string }
    | { by: 'ai'; id: string; confidence: string; reason: string; account: string }
    | null
  exception: { id: string; title: string; explanation: string; source: string; next_step: string } | null
  posting: { line: string; account: string; basis: string; approved_by: string; status: string }
}

export type Anomaly = {
  planted: number
  caught_in_review: number
  found: number
  true_positives: number
  false_positives: number
  missed: number
}

export type Site = {
  meta: { title: string; author: string; subtitle: string; company: string; period: string; period_label: string; fx_downloaded: string; fx_source: string }
  summary: {
    transactions: number
    by_type: Record<string, number>
    receipts: number
    spend_usd: string
    spend_ars: string
    spend_usd_compact: string
    spend_ars_compact: string
    card_net_usd: string
    payouts_usdc: string
    split: Split
    no_touch: number
    no_touch_share: string
    exceptions: number
    threshold: string | null
    ai_confident_but_in_review: number
    closing_rate: string
  }
  flow: Flow
  spend_by_account: SpendRow[]
  examples: Example[]
  queue: QueueItem[]
  journal: {
    groups: { name: string; accounts: string[]; debe: string; haber: string }[]
    rows: { account: string; name: string; debe: string; haber: string; debe_compact: string; haber_compact: string }[]
    totals: { debe: string; haber: string; balanced: boolean; difference: string }
    lines: number
    excel: string
    balances: { opening_rate: string; closing_rate: string }
  }
  eval: {
    extraction: { template: Record<string, string>; ai: Record<string, string> | null; receipts: number }
    matching: { correct: number; total: number; accuracy: string }
    rules: { correct: number; total: number; accuracy: string }
    ai_accounts: { correct: number; total: number; accuracy: string; small_sample: boolean } | null
    ai_resolved: { correct: number; total: number; accuracy: string } | null
    anomalies: Record<string, Anomaly>
    threshold: { rows: ThresholdRow[]; recommended: string | null; why: string; target: string | null; recommended_row: ThresholdRow | null }
    explanations: {
      exceptions: number
      accepted_first_try: number
      accepted_after_retry: number
      fell_back_to_template: number
      rejections_by_reason: Record<string, number>
    } | null
    decision_table: { step: string; handled_by: string; why: string; accuracy: string; headline: string; note: string }[]
    llm_usage: { total_calls: number; total_cost_usd: number; models: Record<string, string>; backend: string } | null
  }
  methodology: { topic: string; label: string; detail: string }[]
  memo?: string
}

export const site = raw as unknown as Site

/** '0.958' -> '95.8%'. Display only. */
export function pct(ratio: string | null | undefined, digits = 1): string {
  if (ratio == null) return 'n/a'
  return `${(Number(ratio) * 100).toFixed(digits)}%`
}
