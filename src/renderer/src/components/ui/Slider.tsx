/* eslint-disable no-unused-vars */
'use client'

import * as React from 'react'
import * as SliderPrimitive from '@radix-ui/react-slider'
import { cn } from '@/lib/utils'

interface SliderProps extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> {
  showValue?: boolean
  formatValue?: (value: number) => string
}

const Slider = React.forwardRef<React.ElementRef<typeof SliderPrimitive.Root>, SliderProps>(
  ({ className, showValue, formatValue, value, defaultValue, ...props }, ref) => {
    const [localValue, setLocalValue] = React.useState<number[]>(
      (value as number[]) || (defaultValue as number[]) || [0]
    )
    const [isDragging, setIsDragging] = React.useState(false)

    React.useEffect(() => {
      if (value !== undefined) {
        setLocalValue(value as number[])
      }
    }, [value])

    const currentValue = localValue[0]
    const formattedValue = formatValue ? formatValue(currentValue) : currentValue.toString()

    return (
      <div className="relative">
        <SliderPrimitive.Root
          ref={ref}
          value={value}
          defaultValue={defaultValue}
          onValueChange={setLocalValue}
          onPointerDown={() => setIsDragging(false)}
          onPointerUp={() => setIsDragging(false)}
          className={cn('relative flex w-full touch-none select-none items-center', className)}
          {...props}
        >
          <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-zinc-700/30">
            <SliderPrimitive.Range className="absolute h-full bg-emerald-500" />
          </SliderPrimitive.Track>
          <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border border-zinc-700/50 bg-emerald-500 shadow-sm ring-offset-background hover:scale-110 hover:bg-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 transition-transform duration-200" />
        </SliderPrimitive.Root>
        {showValue && isDragging && (
          <div
            className="absolute -top-6 left-0 transform -translate-x-1/2 px-2 py-1 rounded-md bg-zinc-800 text-xs text-zinc-100"
            style={{ left: `${currentValue * 100}%` }}
          >
            {formattedValue}
          </div>
        )}
      </div>
    )
  }
)
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
