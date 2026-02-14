"use client";

import { useState } from "react";
import { Plus, X, GripVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface ListEditorProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  label?: string;
  className?: string;
  disabled?: boolean;
}

export function ListEditor({
  value,
  onChange,
  placeholder = "Yeni öğe ekle...",
  label,
  className,
  disabled,
}: ListEditorProps) {
  const [newItem, setNewItem] = useState("");

  const handleAdd = () => {
    if (newItem.trim()) {
      onChange([...value, newItem.trim()]);
      setNewItem("");
    }
  };

  const handleRemove = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium text-stone-700">{label}</label>
      )}

      {/* Existing items */}
      <div className="space-y-1.5">
        {value.map((item, index) => (
          <div
            key={index}
            className="flex items-center gap-2 bg-stone-50 rounded-md px-3 py-2 group"
          >
            <GripVertical className="h-4 w-4 text-stone-300 shrink-0" />
            <span className="flex-1 text-sm text-stone-700">{item}</span>
            {!disabled && (
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="p-0.5 hover:bg-stone-200 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3.5 w-3.5 text-stone-500" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Add new item */}
      {!disabled && (
        <div className="flex gap-2">
          <Input
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="flex-1 bg-white"
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={handleAdd}
            disabled={!newItem.trim()}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      )}

      {value.length === 0 && disabled && (
        <p className="text-sm text-stone-400 italic">Öğe yok</p>
      )}
    </div>
  );
}
