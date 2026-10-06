export interface FrameCacheState {
  images: HTMLImageElement[];
  loadedCount: number;
  totalFrames: number;
  isReady: boolean;
}

export const frameCache: FrameCacheState = {
  images: [],
  loadedCount: 0,
  totalFrames: 240,
  isReady: false,
};
