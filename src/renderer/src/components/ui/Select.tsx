'use client'

import * as React from 'react'
import * as SelectPrimitive from '@radix-ui/react-select'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

const Select = SelectPrimitive.Root

const SelectGroup = SelectPrimitive.Group

const SelectValue = SelectPrimitive.Value

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      'w-full px-3 py-2.5 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-100 text-sm',
      'flex items-center',
      'focus:outline-none focus:ring-1 focus:ring-zinc-600',
      'transition-all duration-200 hover:bg-zinc-800/70',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      className
    )}
    {...props}
  >
    <div className="flex-1 text-left">{children}</div>
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="w-4 h-4 text-zinc-400 transition-transform duration-200 ml-2" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = 'popper', ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        'relative z-50 overflow-hidden',
        'w-[var(--radix-select-trigger-width)]',
        'rounded-lg border border-zinc-700/50 bg-zinc-800/95 backdrop-blur-sm',
        'shadow-lg shadow-black/20',
        'animate-in fade-in-0 zoom-in-95',
        position === 'popper' &&
          'data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1',
        className
      )}
      position={position}
      {...props}
    >
      <SelectPrimitive.Viewport
        className={cn(
          'p-1',
          'max-h-[250px] overflow-y-scroll',
          '[&::-webkit-scrollbar]:w-2',
          '[&::-webkit-scrollbar-track]:bg-zinc-800/30',
          '[&::-webkit-scrollbar-thumb]:bg-zinc-600/50',
          '[&::-webkit-scrollbar-thumb]:rounded-full',
          '[&::-webkit-scrollbar-thumb]:border-2',
          '[&::-webkit-scrollbar-thumb]:border-zinc-800/30',
          'hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50'
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
))
SelectContent.displayName = SelectPrimitive.Content.displayName

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      'relative flex items-center select-none',
      'py-2 pl-3 pr-8 text-sm text-zinc-300',
      'rounded-md cursor-default',
      'focus:bg-zinc-700/50 focus:text-zinc-100 focus:outline-none',
      'data-[disabled]:opacity-50 data-[disabled]:pointer-events-none',
      className
    )}
    {...props}
  >
    <SelectPrimitive.ItemText className="flex-1">{children}</SelectPrimitive.ItemText>
    <span className="absolute right-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4 text-emerald-500" />
      </SelectPrimitive.ItemIndicator>
    </span>
  </SelectPrimitive.Item>
))
SelectItem.displayName = SelectPrimitive.Item.displayName

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn('mx-1 my-1 h-px bg-zinc-700/50', className)}
    {...props}
  />
))
SelectSeparator.displayName = SelectPrimitive.Separator.displayName

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectSeparator
}
