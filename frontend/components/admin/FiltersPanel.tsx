'use client';

import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { useState } from 'react';

export interface FilterValues {
  status: 'all' | 'safe' | 'needs_review' | 'violation' | 'evaluating';
  minScore: number;
  maxScore: number;
  searchQuery: string;
}

interface FiltersPanelProps {
  onFilterChange: (filters: FilterValues) => void;
}

export function FiltersPanel({ onFilterChange }: FiltersPanelProps) {
  const [filters, setFilters] = useState<FilterValues>({
    status: 'all',
    minScore: 0,
    maxScore: 100,
    searchQuery: '',
  });

  const handleStatusChange = (status: string) => {
    const newFilters = {
      ...filters,
      status: status as FilterValues['status'],
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleScoreChange = (value: number[]) => {
    const newFilters = {
      ...filters,
      minScore: value[0],
      maxScore: value[1],
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSearchChange = (query: string) => {
    const newFilters = {
      ...filters,
      searchQuery: query,
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const defaultFilters: FilterValues = {
      status: 'all',
      minScore: 0,
      maxScore: 100,
      searchQuery: '',
    };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  return (
    <Card className="border-border p-6 mb-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">Filters</h3>
      <div className="space-y-4">
        {/* Search Input */}
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-2">
            Search
          </label>
          <Input 
            placeholder="Search by ID or question..." 
            value={filters.searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="bg-transparent"
          />
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-2">
            Status
          </label>
          <div className="flex gap-2 flex-wrap">
            {['all', 'safe', 'needs_review', 'violation'].map((status) => (
              <Button
                key={status}
                variant={filters.status === status ? 'default' : 'outline'}
                size="sm"
                onClick={() =>
                  handleStatusChange(status)
                }
                className={
                  filters.status === status
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }
              >
                {status === 'all'
                  ? 'All'
                  : status === 'safe'
                    ? 'Safe'
                    : status === 'needs_review'
                      ? 'Needs Review'
                      : 'Violation'}
              </Button>
            ))}
          </div>
        </div>

        {/* Score Range */}
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-3">
            Ethical Score Range: {filters.minScore} - {filters.maxScore}
          </label>
          <Slider
            min={0}
            max={100}
            step={5}
            value={[filters.minScore, filters.maxScore]}
            onValueChange={handleScoreChange}
            className="w-full"
          />
        </div>

        {/* Reset Button */}
        <Button
          variant="outline"
          onClick={handleReset}
          className="w-full bg-transparent"
        >
          Reset Filters
        </Button>
      </div>
    </Card>
  );
}
