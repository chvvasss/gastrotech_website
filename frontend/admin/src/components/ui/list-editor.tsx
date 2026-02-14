"use client";

import { useState, useCallback } from "react";
import { Plus, X, GripVertical } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";
import { cn } from "@/lib/utils";

interface ListEditorProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  maxItems?: number;
  maxLength?: number;
  className?: string;
  disabled?: boolean;
}

export function ListEditor({
  value = [],
  onChange,
  placeholder = "Yeni öğe ekle...",
  maxItems = 20,
  maxLength = 500,
  className,
  disabled = false,
}: ListEditorProps) {
  const [newItem, setNewItem] = useState("");

  const handleAddItem = useCallback(() => {
    const trimmed = newItem.trim();
    if (!trimmed || value.length >= maxItems) return;
    onChange([...value, trimmed]);
    setNewItem("");
  }, [newItem, value, maxItems, onChange]);

  const handleRemoveItem = useCallback(
    (index: number) => {
      const newValue = [...value];
      newValue.splice(index, 1);
      onChange(newValue);
    },
    [value, onChange]
  );

  const handleUpdateItem = useCallback(
    (index: number, newText: string) => {
      const newValue = [...value];
      newValue[index] = newText;
      onChange(newValue);
    },
    [value, onChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleAddItem();
      }
    },
    [handleAddItem]
  );

  return (
    <div className={cn("space-y-2", className)}>
      {/* Existing items */}
      <div className="space-y-1">
        {value.map((item, index) => (
          <div
            key={index}
            className="flex items-center gap-2 p-2 bg-stone-50 rounded-lg group"
          >
            <GripVertical className="h-4 w-4 text-stone-300 flex-shrink-0" />
            <Input
              value={item}
              onChange={(e) => handleUpdateItem(index, e.target.value)}
              disabled={disabled}
              maxLength={maxLength}
              className="flex-1 h-8 text-sm bg-white"
            />
            {!disabled && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleRemoveItem(index)}
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-stone-400 hover:text-red-500"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        ))}
      </div>

      {/* Add new item */}
      {!disabled && value.length < maxItems && (
        <div className="flex gap-2">
          <Input
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            maxLength={maxLength}
            className="flex-1 h-9 text-sm"
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddItem}
            disabled={!newItem.trim()}
            className="h-9"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Item count */}
      <p className="text-xs text-stone-400">
        {value.length} / {maxItems} öğe
      </p>
    </div>
  );
}
