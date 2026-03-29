import { Image } from 'react-konva'
import useImage from 'use-image'

interface FloorPlanImageProps {
  imageUrl: string
  width: number
  height: number
}

export function FloorPlanImage({ imageUrl, width, height }: FloorPlanImageProps) {
  const [image] = useImage(imageUrl, 'anonymous')

  return <Image image={image} width={width} height={height} />
}
