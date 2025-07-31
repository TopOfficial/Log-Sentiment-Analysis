"use client";

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import React, { useState } from "react";
import { cn } from "@/lib/utils";

type ComboboxProps = {
  options: string[];
  placeholder?: string;
  onChange: (value: string) => void;
};

export function Combobox({ options, placeholder, onChange }: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState("");

  const safeOptions = options.filter((opt): opt is string => typeof opt === 'string' && opt.trim() !== "")

  const handleSelect = (value: string) => {
    setSelected(value);
    onChange(value);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {selected || placeholder || "Select..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder="Search or add..." />
          <CommandEmpty>No match. Press enter to add.</CommandEmpty>
          <CommandGroup>
            {safeOptions.map((option) => (
              <CommandItem
                key={option}
                value={option}
                onSelect={() => handleSelect(option)}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    selected === option ? "opacity-100" : "opacity-0"
                  )}
                />
                {option}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}