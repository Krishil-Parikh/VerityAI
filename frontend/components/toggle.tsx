"use client"

import { useState, useEffect } from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { cn } from "@/lib/utils"

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const isDark = theme === "dark"

  return (
    <div
      className={cn(
        "flex w-20 h-11 p-1 rounded-full cursor-pointer transition-all duration-300",
        isDark
          ? "bg-zinc-950 border border-zinc-800"
          : "bg-zinc-100 border border-zinc-200",
        className
      )}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      role="button"
      tabIndex={0}
    >
      <div className="flex justify-between items-center w-full">
        <div
          className={cn(
            "flex justify-center items-center w-8 h-8 rounded-full transition-transform duration-300",
            isDark
              ? "transform translate-x-0 bg-zinc-800"
              : "transform translate-x-10 bg-gray-200"
          )}
        >
          {isDark ? (
            <Moon
              className="w-5 h-5 text-white"
              strokeWidth={1.5}
            />
          ) : (
            <Sun
              className="w-5 h-5 text-gray-700"
              strokeWidth={1.5}
            />
          )}
        </div>
        <div
          className={cn(
            "flex justify-center items-center w-8 h-8 rounded-full transition-transform duration-300",
            isDark
              ? "bg-transparent"
              : "transform -translate-x-10"
          )}
        >
          {isDark ? (
            <Sun
              className="w-5 h-5 text-gray-500"
              strokeWidth={1.5}
            />
          ) : (
            <Moon
              className="w-5 h-5 text-black"
              strokeWidth={1.5}
            />
          )}
        </div>
      </div>
    </div>
  )
}