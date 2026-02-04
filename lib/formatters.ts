export const formatDate = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatNumber = (num: number, decimals = 0): string => {
  return num.toFixed(decimals);
};

export const truncateText = (text: string, length: number): string => {
  return text.length > length ? text.substring(0, length) + '...' : text;
};

export const getStatusLabel = (
  status: 'safe' | 'needs_review' | 'violation' | 'evaluating'
): string => {
  const labels = {
    safe: 'Safe',
    needs_review: 'Needs Review',
    violation: 'Violation',
    evaluating: 'Evaluating',
  };
  return labels[status];
};

export const getScoreStatus = (score: number): 'safe' | 'needs_review' | 'violation' => {
  if (score >= 85) return 'safe';
  if (score >= 70) return 'needs_review';
  return 'violation';
};
