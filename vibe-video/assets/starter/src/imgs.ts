// 由 scripts/prep_images.py 生成：public/cut 里每张图的宽高比（宽/高）。素材入库前为空
export const ASPECT = {} as const;
export type ImgName = keyof typeof ASPECT;
