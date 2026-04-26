import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, ChevronRight, Calculator, PieChart } from 'lucide-react';
import api from '../utils/api';

const GoalTracker = ({ goals = [], compact = false }) => {
  const [activeGoals, setActiveGoals] = useState(goals);

  useEffect(() => {
    if (goals.length > 0) {
      setActiveGoals(goals);
    } else {
      fetchGoals();
    }
  }, [goals]);

  const fetchGoals = async () => {
    try {
      const response = await api.getGoals();
      setActiveGoals(response.data.goals || []);
    } catch (error) {
      console.error('Error fetching goals for tracker:', error);
    }
  };

  if (!activeGoals || activeGoals.length === 0) {
    return (
      <div className="bg-retro-surface/80 rounded-xl border border-brand-1/20 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Target className="w-5 h-5 text-brand-1" />
          <h3 className="font-bold text-text-main">Goal Tracker</h3>
        </div>
        <p className="text-text-muted text-sm italic">No active goals yet. Set your first goal to track progress!</p>
      </div>
    );
  }

  return (
    <div className="bg-retro-surface/80 rounded-xl border border-brand-1/20 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-brand-1" />
          <h3 className="font-bold text-text-main">Goal Tracker</h3>
        </div>
        <span className="text-[10px] font-bold px-2 py-0.5 bg-brand-1/10 text-brand-1 rounded-full uppercase tracking-tighter">
          {activeGoals.length} Active
        </span>
      </div>

      <div className="space-y-4">
        {activeGoals.slice(0, compact ? 2 : 5).map((goal) => {
          const progress = Math.min(100, (goal.current_amount / goal.target_amount) * 100);
          
          return (
            <div key={goal.id} className="group cursor-pointer">
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-sm font-bold text-text-main flex items-center gap-2">
                  {goal.name}
                  {progress >= 100 && <span className="text-[8px] bg-emerald-100 text-emerald-600 px-1 rounded">GOAL MET</span>}
                </span>
                <span className="text-xs font-semibold text-text-muted">
                  {Math.round(progress)}%
                </span>
              </div>
              
              <div className="h-2 w-full bg-brand-1/5 rounded-full overflow-hidden border border-brand-1/10">
                <div 
                  className="h-full bg-gradient-to-r from-brand-1 to-brand-600 transition-all duration-1000"
                  style={{ width: `${progress}%` }}
                />
              </div>
              
              <div className="flex justify-between mt-2 text-[10px] text-text-muted font-medium">
                <span>₹{goal.current_amount?.toLocaleString()}</span>
                <span>Target: ₹{goal.target_amount?.toLocaleString()}</span>
              </div>
            </div>
          );
        })}
      </div>

      {!compact && (
        <div className="pt-4 border-t border-brand-1/10">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-brand-1/5 p-3 rounded-lg border border-brand-1/10">
              <div className="flex items-center gap-2 text-[10px] font-bold text-brand-1 uppercase mb-1">
                <Calculator className="w-3 h-3" /> Total Target
              </div>
              <div className="font-bold text-sm text-text-main">
                ₹{activeGoals.reduce((sum, g) => sum + g.target_amount, 0).toLocaleString()}
              </div>
            </div>
            <div className="bg-brand-1/5 p-3 rounded-lg border border-brand-1/10">
              <div className="flex items-center gap-2 text-[10px] font-bold text-brand-1 uppercase mb-1">
                <TrendingUp className="w-3 h-3" /> Monthly SIP
              </div>
              <div className="font-bold text-sm text-text-main">
                ₹{activeGoals.reduce((sum, g) => sum + (g.monthly_sip || 0), 0).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GoalTracker;
