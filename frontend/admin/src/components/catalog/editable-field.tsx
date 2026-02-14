"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface EditableFieldProps {
  label: string;
  value: string | number | boolean | null | undefined;
  onChange: (value: string | number | boolean) => void;
  type?: "text" | "number" | "textarea" | "select" | "switch";
  options?: { value: string; label: string }[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  className?: string;
}

export function EditableField({
  label,
  value,
  onChange,
  type = "text",
  options,
  placeholder,
  disabled,
  required,
  error,
  className,
}: EditableFieldProps) {
  const id = label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={id} className="text-sm font-medium text-stone-700">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </Label>

      {type === "text" && (
        <Input
          id={id}
          value={(value as string) || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn("bg-white", error && "border-red-500")}
        />
      )}

      {type === "number" && (
        <Input
          id={id}
          type="number"
          value={value !== null && value !== undefined ? String(value) : ""}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
          placeholder={placeholder}
          disabled={disabled}
          className={cn("bg-white", error && "border-red-500")}
        />
      )}

      {type === "textarea" && (
        <Textarea
          id={id}
          value={(value as string) || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn("bg-white min-h-[100px]", error && "border-red-500")}
        />
      )}

      {type === "select" && options && (
        <Select
          value={(value as string) || ""}
          onValueChange={onChange}
          disabled={disabled}
        >
          <SelectTrigger className={cn("bg-white", error && "border-red-500")}>
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {type === "switch" && (
        <div className="flex items-center gap-2">
          <Switch
            id={id}
            checked={Boolean(value)}
            onCheckedChange={onChange}
            disabled={disabled}
          />
          <span className="text-sm text-stone-600">
            {value ? "Evet" : "Hayır"}
          </span>
        </div>
      )}

      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
