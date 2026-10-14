// The profile photo is cut to a centred square and shrunk here, so what goes up is a small JPEG
// whatever the camera made. The server checks it again (backend/app/avatars.py).
export const ACCEPT = 'image/jpeg,image/png,image/webp'
const SIZE = 256
const QUALITY = 0.85

export async function squareJpeg(file) {
  // 'from-image' applies the EXIF rotation, so a phone's portrait comes out upright.
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  try {
    const side = Math.min(bitmap.width, bitmap.height)
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = SIZE
    const context = canvas.getContext('2d')
    context.imageSmoothingQuality = 'high'
    context.drawImage(
      bitmap,
      (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side,
      0, 0, SIZE, SIZE,
    )
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITY))
    if (!blob) throw new Error('toBlob failed')
    return blob
  } finally {
    bitmap.close()
  }
}
