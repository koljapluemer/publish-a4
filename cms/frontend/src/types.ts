export interface Placement {
  name: string
  top: number
  left: number
}

export interface Card extends Placement {
  source: string
}

export interface Collage {
  name: string
  cards: Placement[]
}

export interface PreviewMessage {
  source: 'a4-preview'
  type: 'card-selected' | 'card-moved' | 'save-error'
  card?: string
  top?: number
  left?: number
  message?: string
}
