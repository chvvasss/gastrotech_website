"use client";

import { useState, useMemo } from "react";
import { ChevronRight, ChevronDown, Leaf, FolderTree } from "lucide-react";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import type { TaxonomyNode } from "@/types/api";

interface TreeNodeRowProps {
  node: TaxonomyNode;
  level: number;
  selectedLeafSlugs: Set<string>;
  onToggleSelect: (slug: string) => void;
  searchTerm?: string;
}

function TreeNodeRow({
  node,
  level,
  selectedLeafSlugs,
  onToggleSelect,
  searchTerm,
}: TreeNodeRowProps) {
  const [expanded, setExpanded] = useState(level < 2);
  const isLeaf = !node.children || node.children.length === 0;
  const isSelected = selectedLeafSlugs.has(node.slug);
  const hasChildren = node.children && node.children.length > 0;

  // Check if node matches search
  const matchesSearch = !searchTerm || 
    node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.slug.toLowerCase().includes(searchTerm.toLowerCase());

  // Check if any child matches search
  const hasMatchingChildren = useMemo(() => {
    if (!searchTerm || !node.children) return true;
    
    const checkChildren = (children: TaxonomyNode[]): boolean => {
      for (const child of children) {
        if (child.name.toLowerCase().includes(searchTerm.toLowerCase())) {
          return true;
        }
        if (child.children && checkChildren(child.children)) {
          return true;
        }
      }
      return false;
    };
    
    return checkChildren(node.children);
  }, [node.children, searchTerm]);

  // Hide if doesn't match and no children match
  if (searchTerm && !matchesSearch && !hasMatchingChildren) {
    return null;
  }

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-stone-50 transition-colors",
          isSelected && "bg-primary/5",
          matchesSearch && searchTerm && "bg-amber-50"
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {/* Expand/Collapse button */}
        {hasChildren ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-0.5 hover:bg-stone-200 rounded transition-colors"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-stone-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-stone-500" />
            )}
          </button>
        ) : (
          <span className="w-5" />
        )}

        {/* Checkbox for leaf nodes */}
        {isLeaf ? (
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleSelect(node.slug)}
            className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
          />
        ) : (
          <FolderTree className="h-4 w-4 text-stone-400" />
        )}

        {/* Node name */}
        <span
          className={cn(
            "text-sm flex-1",
            isLeaf ? "text-stone-900" : "text-stone-600 font-medium"
          )}
        >
          {node.name}
        </span>

        {/* Leaf badge */}
        {isLeaf && (
          <Badge variant="outline" className="text-xs px-1.5 py-0 h-5 bg-green-50 text-green-700 border-green-200">
            <Leaf className="h-3 w-3 mr-0.5" />
            leaf
          </Badge>
        )}
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <div>
          {node.children.map((child) => (
            <TreeNodeRow
              key={child.slug}
              node={child}
              level={level + 1}
              selectedLeafSlugs={selectedLeafSlugs}
              onToggleSelect={onToggleSelect}
              searchTerm={searchTerm}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface TreeViewProps {
  nodes: TaxonomyNode[];
  selectedLeafSlugs: Set<string>;
  onToggleSelect: (slug: string) => void;
  searchTerm?: string;
}

export function TreeView({
  nodes,
  selectedLeafSlugs,
  onToggleSelect,
  searchTerm,
}: TreeViewProps) {
  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FolderTree className="h-12 w-12 text-stone-300 mb-4" />
        <p className="text-stone-500">Taksonomi düğümü bulunamadı</p>
        <p className="text-sm text-stone-400">Bir seri seçin</p>
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {nodes.map((node) => (
        <TreeNodeRow
          key={node.slug}
          node={node}
          level={0}
          selectedLeafSlugs={selectedLeafSlugs}
          onToggleSelect={onToggleSelect}
          searchTerm={searchTerm}
        />
      ))}
    </div>
  );
}
