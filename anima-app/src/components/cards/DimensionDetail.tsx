import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { X, Wind, ChatTeardrop, Plus, Fire, Check, Moon, Drop, ForkKnife, Barbell, Timer, Brain } from '@phosphor-icons/react';
import type { DimConfig } from '../../lib/dimensions';
import type { DimModel } from '../../lib/lifeModel';
import { getSleepReport, getHydrationReport, getNutritionReport, getFitnessReport, getFocusReport, getMentalReport } from '../../lib/api';
import { FocusTimer } from '../session/FocusTimer';
import { DimBells } from '../bells/Bells';

export function DimensionDetail({
  cfg, model, data, records, onClose, onLog, onBreathe, onCheckin,
}: {
  cfg: DimConfig; model: DimModel; data: any; records: any;
  onClose: () => void;
  onLog: (kind: string, payload: any) => void;
  onBreathe: () => void;
  onCheckin: () => void;
}) {
  const unit = data?.unit || model.unit;
  const today = data?.today ?? null;
  const isGoals = model.id === 'goals';
  const isHabits = model.id === 'habits';
  const isSleep = model.id === 'sleep';
  const isHydration = model.id === 'hydration';
  const isNutrition = model.id === 'nutrition';
  const isFitness = model.id === 'fitness';
  const isFocus = model.id === 'focus';
  const isMental = model.id === 'mental';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 overflow-y-auto bg-bg">
      <div className="pointer-events-none fixed inset-0"
        style={{ background: `radial-gradient(120% 70% at 50% -10%, color-mix(in srgb, ${cfg.accent} 14%, transparent), transparent 60%)` }} />
      <div className="relative mx-auto max-w-md px-5 pb-12 pt-6">
        <div className="flex items-center justify-between">
          <button onClick={onClose} className="flex items-center gap-1.5 text-sm text-faint transition-colors hover:text-lantern">
            <X size={18} weight="light" /> back
          </button>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <span className="grid h-12 w-12 place-items-center rounded-full"
            style={{ backgroundColor: `color-mix(in srgb, ${cfg.accent} 16%, transparent)` }}>
            <cfg.icon size={26} weight="light" style={{ color: cfg.accent }} />
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-faint">{cfg.label}</p>
            <p className="font-wizard text-[30px] leading-none text-ink">
              {today != null ? Number(today) : '—'}<span className="ml-1 align-top text-sm text-faint">{unit}</span>
            </p>
          </div>
        </div>

        <p className="mt-3 font-wizard text-[15px] leading-snug text-muted">{model.opener}</p>
        <DimBells dim={model.id} />

        {isGoals && <GoalsSection records={records} onLog={onLog} />}
        {isHabits && <HabitsSection records={records} onLog={onLog} />}
        {isSleep && <SleepSection onLog={onLog} />}
        {isHydration && <HydrationSection onLog={onLog} />}
        {isNutrition && <NutritionSection onLog={onLog} />}
        {isFitness && <FitnessSection onLog={onLog} />}
        {isFocus && <FocusSection onLog={onLog} />}
        {isMental && <MentalSection onLog={onLog} />}
        {!isGoals && !isHabits && !isSleep && !isHydration && !isNutrition && !isFitness && !isFocus && !isMental && <GenericSection model={model} records={records} onLog={onLog} />}

        <div className="mt-6 flex flex-wrap gap-2">
          <button onClick={onBreathe}
            className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
            <Wind size={16} weight="light" /> A calming breath
          </button>
          <button onClick={onCheckin}
            className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2.5 text-sm text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
            <ChatTeardrop size={16} weight="light" /> Check in with the wizard
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function GoalRing({ pct, done }: { pct: number; done?: boolean }) {
  const r = 15;
  const c = 2 * Math.PI * r;
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" className="shrink-0">
      <circle cx="20" cy="20" r={r} fill="none" stroke="var(--line)" strokeWidth="4" />
      <circle cx="20" cy="20" r={r} fill="none" stroke={done ? 'var(--sage)' : 'var(--lantern)'} strokeWidth="4"
        strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
        transform="rotate(-90 20 20)" style={{ transition: 'stroke-dashoffset 0.5s ease' }} />
      <text x="20" y="24" textAnchor="middle" fontSize="10" fontWeight="600"
        fill={done ? 'var(--sage)' : 'var(--ink)'}>{pct}</text>
    </svg>
  );
}

function GoalRow({ goal, onLog }: { goal: any; onLog: (k: string, p: any) => void }) {
  const steps = goal.steps || [];
  const isSteps = steps.length > 0;
  const target = Number(goal.target) || 0;
  const count = Number(goal.count) || 0;
  const pct = Math.min(100, Math.round(Number(goal.pct) || 0));
  const done = pct >= 100;
  const isCount = !goal.source && !isSteps;
  const isHabit = (goal.source || '').startsWith('habit:');
  const isDim = (goal.source || '').startsWith('dim:');
  const [settingTarget, setSettingTarget] = useState(false);
  const [tVal, setTVal] = useState('');
  const [tUnit, setTUnit] = useState('');
  const [editing, setEditing] = useState(false);
  const [editVal, setEditVal] = useState('');
  const [confirmDel, setConfirmDel] = useState(false);
  const [showSteps, setShowSteps] = useState(false);
  const [newStep, setNewStep] = useState('');

  return (
    <div className="rounded-card border border-line bg-surface p-4 transition-colors"
      style={done ? {
        borderColor: 'color-mix(in srgb, var(--sage) 50%, var(--line))',
        background: 'color-mix(in srgb, var(--sage) 6%, var(--surface))',
      } : undefined}>
      <div className="flex items-start gap-3">
        <GoalRing pct={pct} done={done} />
        <div className="min-w-0 flex-1">
          <p className="font-medium leading-snug text-ink">{done && <span className="mr-1">🎉</span>}{goal.name}</p>
          <p className="text-xs text-faint">
            {isSteps ? `${count} of ${target} steps` : (target ? `${count} of ${target} ${goal.unit || 'steps'}` : `${count} done`)}
          </p>
        </div>
        {isCount && !done && (
          <button onClick={() => onLog('goal_inc', { goal_name: goal.name })}
            className="shrink-0 rounded-full bg-lantern px-3 py-1.5 text-xs font-medium text-bg transition-all hover:bg-ember">
            +1 {goal.unit || 'step'}
          </button>
        )}
        {done && <span className="shrink-0 text-[11px] font-medium" style={{ color: 'var(--sage)' }}>Completed</span>}
      </div>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-line/40">
        <div className="h-full rounded-full transition-all duration-500"
          style={{ width: pct + '%', background: done ? 'var(--sage)' : 'var(--lantern)' }} />
      </div>

      {done ? (
        <p className="mt-2 text-xs" style={{ color: 'var(--sage)' }}>
          Completed — beautifully done. Let it rest, or start the next one.
        </p>
      ) : isSteps ? (
        <div className="mt-3 space-y-2">
          {goal.next_step && (
            <div className="flex items-center justify-between gap-2 rounded-xl border border-lantern/30 bg-bg px-3 py-2">
              <p className="min-w-0 truncate text-[12px] text-muted">next rung: <span className="text-ink">{goal.next_step.name}</span></p>
              <button onClick={() => onLog('goal_step', { goal_name: goal.name, index: goal.next_step.index, done: true })}
                className="shrink-0 rounded-full bg-lantern px-3 py-1 text-[11px] font-medium text-bg transition-all hover:bg-ember">
                mark done
              </button>
            </div>
          )}
          <button onClick={() => setShowSteps(v => !v)}
            className="text-[11px] text-faint underline-offset-2 transition-colors hover:text-lantern hover:underline">
            {showSteps ? 'hide the ladder' : `view the ladder (${count} of ${target})`}
          </button>
          {showSteps && (
            <div className="space-y-1.5">
              {steps.map((st: any, i: number) => (
                <button key={i} onClick={() => onLog('goal_step', { goal_name: goal.name, index: i, done: !st.done })}
                  className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[12px] transition-colors hover:bg-bg">
                  <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full border"
                    style={{ borderColor: st.done ? 'var(--sage)' : 'var(--line)', background: st.done ? 'var(--sage)' : 'transparent' }}>
                    {st.done && <Check size={10} weight="bold" style={{ color: 'var(--bg)' }} />}
                  </span>
                  <span className={st.done ? 'text-faint line-through' : 'text-muted'}>{st.name}</span>
                </button>
              ))}
              <div className="flex gap-2 pt-1">
                <input value={newStep} onChange={(e) => setNewStep(e.target.value)} placeholder="add a step…"
                  className="min-w-0 flex-1 rounded-lg border border-line bg-bg px-2 py-1.5 text-xs text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
                <button onClick={() => { if (newStep.trim()) { onLog('goal_add_step', { goal_name: goal.name, step_name: newStep.trim() }); setNewStep(''); } }}
                  className="rounded-full bg-lantern px-3 py-1.5 text-[11px] font-medium text-bg">add</button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <>
          {goal.pace && <p className="mt-2 text-xs text-muted">{goal.pace}</p>}
          {isHabit && <p className="mt-2 text-[11px] text-faint">fed by your habit “{String(goal.source).slice(6)}” — mark it done and this fills.</p>}
          {isDim && <p className="mt-2 text-[11px] text-faint">counted automatically from {String(goal.source).slice(4)} this week.</p>}

          {isCount && !target && (
            settingTarget ? (
              <div className="mt-3 flex gap-2">
                <input value={tVal} onChange={(e) => setTVal(e.target.value)} type="number" placeholder="Target"
                  className="w-20 rounded-lg border border-line bg-bg px-2 py-1.5 text-xs text-ink outline-none focus:border-lantern/60" />
                <input value={tUnit} onChange={(e) => setTUnit(e.target.value)} placeholder="unit"
                  className="flex-1 rounded-lg border border-line bg-bg px-2 py-1.5 text-xs text-ink outline-none focus:border-lantern/60" />
                <button onClick={() => { if (tVal) { onLog('goal', { goal_name: goal.name, target: Number(tVal), unit: tUnit.trim() || 'steps' }); setSettingTarget(false); } }}
                  className="rounded-full bg-lantern px-3 py-1.5 text-xs font-medium text-bg">Set</button>
              </div>
            ) : (
              <button onClick={() => setSettingTarget(true)}
                className="mt-2 text-[11px] text-faint underline-offset-2 transition-colors hover:text-lantern hover:underline">
                give it a target so the ring can fill →
              </button>
            )
          )}

          {!isHabit && goal.habit_hint && (
            <div className="mt-3 flex items-center justify-between gap-2 rounded-xl border border-line bg-bg px-3 py-2">
              <p className="min-w-0 truncate text-[11px] text-muted">A habit that helps: {goal.habit_hint}</p>
              <button onClick={() => onLog('goal_link_habit', { goal_name: goal.name, habit_name: goal.habit_hint })}
                className="shrink-0 rounded-full px-3 py-1 text-[11px] font-medium transition-all hover:-translate-y-0.5"
                style={{ background: 'color-mix(in srgb, var(--sage) 20%, transparent)', color: 'var(--sage)' }}>
                Add to my habits
              </button>
            </div>
          )}
        </>
      )}

      <div className="mt-3 flex items-center gap-3 border-t border-line/50 pt-2">
        {editing ? (
          <>
            <input value={editVal} onChange={(e) => setEditVal(e.target.value)} autoFocus
              className="min-w-0 flex-1 rounded-lg border border-line bg-bg px-2 py-1.5 text-xs text-ink outline-none focus:border-lantern/60" />
            <button onClick={() => { if (editVal.trim()) { onLog('goal_rename', { goal_name: goal.name, new_name: editVal.trim() }); setEditing(false); } }}
              className="rounded-full bg-lantern px-3 py-1 text-[11px] font-medium text-bg">Save</button>
            <button onClick={() => setEditing(false)} className="text-[11px] text-faint">✕</button>
          </>
        ) : (
          <>
            <button onClick={() => { setEditVal(goal.name); setEditing(true); }}
              className="text-[11px] text-faint underline-offset-2 transition-colors hover:text-lantern hover:underline">rename</button>
            {confirmDel ? (
              <button onClick={() => onLog('goal_delete', { goal_name: goal.name })}
                className="text-[11px] font-medium" style={{ color: 'var(--mood-angry)' }}>discard for sure?</button>
            ) : (
              <button onClick={() => setConfirmDel(true)}
                className="text-[11px] text-faint underline-offset-2 transition-colors hover:text-mood-angry hover:underline">discard</button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function GoalsSection({ records, onLog }: { records: any; onLog: (k: string, p: any) => void }) {
  const goals = records?.items || [];
  const templates = records?.templates || [];
  const completed = goals.filter((g: any) => (g.pct || 0) >= 100).length;
  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [unit, setUnit] = useState('');
  const [note, setNote] = useState('');
  const [stepsText, setStepsText] = useState('');
  const asLadder = stepsText.trim().length > 0;
  return (
    <div className="mt-5 space-y-3">
      <p className="text-[11px] uppercase tracking-[0.2em] text-faint">Your goals</p>
      {goals.length === 0 && <p className="text-sm text-faint">No goals yet — pick a template or start your own.</p>}
      {goals.map((g: any) => <GoalRow key={(g.name || '') + (g.created || '')} goal={g} onLog={onLog} />)}
      {completed > 0 && (
        <p className="text-xs" style={{ color: 'var(--sage)' }}>🎉 {completed} completed — kept, not forgotten.</p>
      )}

      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-xs text-faint">Let Motif count for you</p>
        <div className="flex flex-wrap gap-2">
          {templates.map((t: any) => (
            <button key={t.name}
              onClick={() => onLog('goal', { name: t.name, unit: t.unit, target: t.target, source: t.source, unit_target: t.unit_target })}
              className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
              {t.label}
            </button>
          ))}
        </div>

        <p className="mb-2 mt-4 text-xs text-faint">Or start your own</p>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="What are you working toward?"
          className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        <textarea value={stepsText} onChange={(e) => setStepsText(e.target.value)} rows={2}
          placeholder="steps, one per line (optional — turns it into a gentle ladder)"
          className="mt-2 w-full resize-none rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        {!asLadder && (
          <div className="mt-2 flex gap-2">
            <input value={target} onChange={(e) => setTarget(e.target.value)} type="number" placeholder="Target"
              className="w-24 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
            <input value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="unit (books)"
              className="flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
          </div>
        )}
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="A note (optional)"
          className="mt-2 w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        <button onClick={() => {
          if (name.trim()) {
            onLog('goal', {
              name: name.trim(),
              steps: asLadder ? stepsText : undefined,
              target: asLadder ? undefined : (target ? Number(target) : undefined),
              unit: asLadder ? undefined : (unit.trim() || undefined),
              note: note.trim() || undefined,
            });
            setName(''); setTarget(''); setUnit(''); setNote(''); setStepsText('');
          }
        }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2 text-sm font-medium text-bg transition-all hover:bg-ember">
          <Plus size={16} weight="light" /> {asLadder ? 'Add ladder' : 'Add goal'}
        </button>
      </div>
    </div>
  );
}

function isoLocal(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
function last7(): string[] {
  const out: string[] = [];
  for (let i = 6; i >= 0; i--) out.push(isoLocal(new Date(Date.now() - i * 86400000)));
  return out;
}

function HabitRow({ habit, onLog }: { habit: any; onLog: (k: string, p: any) => void }) {
  const hist = new Set<string>(habit.history || []);
  const days = last7();
  const today = isoLocal(new Date());
  const doneToday = hist.has(today);
  const streak = Math.round(Number(habit.streak) || 0);
  const flame = streak >= 14 ? 'var(--mood-angry)' : streak >= 7 ? 'var(--lantern)' : streak >= 3 ? 'var(--sage)' : 'var(--faint)';
  const [editing, setEditing] = useState(false);
  const [editVal, setEditVal] = useState('');
  const [confirmDel, setConfirmDel] = useState(false);

  return (
    <div className="rounded-card border border-line bg-surface p-4">
      <div className="flex items-center gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full"
          style={{ backgroundColor: `color-mix(in srgb, ${flame} 16%, transparent)` }}>
          <Fire size={20} weight={streak > 0 ? 'fill' : 'light'} style={{ color: flame }} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-ink">{habit.name}</p>
          <p className="text-xs text-faint">{streak}-day streak · best {habit.best_streak || 0}</p>
        </div>
        {doneToday ? (
          <button onClick={() => onLog('habit_unmark', { habit_name: habit.name })}
            title="tap to undo"
            className="shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-all hover:opacity-80"
            style={{ background: 'color-mix(in srgb, var(--sage) 20%, transparent)', color: 'var(--sage)' }}>
            done today ✓
          </button>
        ) : (
          <button onClick={() => onLog('habit', { habit_name: habit.name, completed: true })}
            className="shrink-0 rounded-full px-4 py-1.5 text-xs font-medium transition-all hover:-translate-y-0.5"
            style={{ background: 'var(--sage)', color: 'var(--bg)' }}>
            Mark done
          </button>
        )}
      </div>

      <div className="mt-3 flex justify-between">
        {days.map((d) => {
          const on = hist.has(d);
          const wd = new Date(d + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'narrow' });
          return (
            <div key={d} className="flex flex-col items-center gap-1">
              <span className="grid h-6 w-6 place-items-center rounded-full border transition-colors"
                style={{ borderColor: on ? 'var(--sage)' : 'var(--line)', background: on ? 'color-mix(in srgb, var(--sage) 30%, transparent)' : 'transparent' }}>
                {on && <Check size={12} weight="bold" style={{ color: 'var(--sage)' }} />}
              </span>
              <span className="text-[9px] text-faint">{wd}</span>
            </div>
          );
        })}
      </div>

      {streak > 0 && !doneToday && (
        <p className="mt-2 text-[11px] text-faint">your streak is alive — one more today keeps the chain.</p>
      )}

      <div className="mt-3 flex items-center gap-3 border-t border-line/50 pt-2">
        {editing ? (
          <>
            <input value={editVal} onChange={(e) => setEditVal(e.target.value)} autoFocus
              className="min-w-0 flex-1 rounded-lg border border-line bg-bg px-2 py-1.5 text-xs text-ink outline-none focus:border-lantern/60" />
            <button onClick={() => { if (editVal.trim()) { onLog('habit_rename', { habit_name: habit.name, new_name: editVal.trim() }); setEditing(false); } }}
              className="rounded-full bg-lantern px-3 py-1 text-[11px] font-medium text-bg">Save</button>
            <button onClick={() => setEditing(false)} className="text-[11px] text-faint">✕</button>
          </>
        ) : (
          <>
            <button onClick={() => { setEditVal(habit.name); setEditing(true); }}
              className="text-[11px] text-faint underline-offset-2 transition-colors hover:text-lantern hover:underline">rename</button>
            {confirmDel ? (
              <button onClick={() => onLog('habit_delete', { habit_name: habit.name })}
                className="text-[11px] font-medium" style={{ color: 'var(--mood-angry)' }}>discard for sure?</button>
            ) : (
              <button onClick={() => setConfirmDel(true)}
                className="text-[11px] text-faint underline-offset-2 transition-colors hover:text-mood-angry hover:underline">discard</button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function HabitsSection({ records, onLog }: { records: any; onLog: (k: string, p: any) => void }) {
  const habits = records?.items || [];
  const [name, setName] = useState('');
  return (
    <div className="mt-5 space-y-3">
      <p className="text-[11px] uppercase tracking-[0.2em] text-faint">Your habits</p>
      {habits.length === 0 && <p className="text-sm text-faint">No habits yet — plant one below.</p>}
      {habits.map((h: any) => <HabitRow key={(h.name || '') + (h.created || '')} habit={h} onLog={onLog} />)}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-xs text-faint">Plant a new habit</p>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Morning walk"
          className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        <button onClick={() => { if (name.trim()) { onLog('habit', { habit_name: name.trim(), completed: false }); setName(''); } }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2 text-sm font-medium text-bg transition-all hover:bg-ember">
          <Plus size={16} weight="light" /> Add habit
        </button>
      </div>
    </div>
  );
}

function qualityColor(q: number | null): string {
  if (q == null) return 'var(--line)';
  if (q >= 7) return 'var(--sage)';
  if (q >= 5) return 'var(--mood-calm)';
  return 'var(--ember)';
}
function fmtNight(d: string): string {
  return new Date(d + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' });
}
function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded-card border border-line bg-surface px-3 py-2.5 text-center">
      <p className="font-wizard text-[18px] text-ink">{value}</p>
      <p className="text-[10px] uppercase tracking-wider text-faint">{label}</p>
    </div>
  );
}

function SleepSection({ onLog }: { onLog: (k: string, p: any) => void }) {
  const [rep, setRep] = useState<any>(null);
  const [hours, setHours] = useState(7.5);
  const [quality, setQuality] = useState(7);
  useEffect(() => { getSleepReport().then(setRep).catch(() => {}); }, []);
  const refresh = async () => { const r = await getSleepReport().catch(() => null); if (r) setRep(r); };
  const log = async (kind: string, payload: any) => { await onLog(kind, payload); await refresh(); };
  if (!rep) return <div className="mt-5 grid h-24 place-items-center text-sm text-faint">gathering your nights…</div>;
  const week = rep.week || [];
  return (
    <div className="mt-5 space-y-3">
      {/* the week of nights */}
      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week of nights</p>
          <p className="text-xs text-faint">{rep.good_week} good night{rep.good_week === 1 ? '' : 's'}</p>
        </div>
        <div className="mt-4 flex h-28 items-end justify-between gap-1.5">
          {week.map((n: any) => {
            const on = n.hours != null;
            const height = on ? Math.max(8, (n.hours / 10) * 100) : 4;
            const wd = new Date(n.date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'narrow' });
            return (
              <div key={n.date} className="flex h-full flex-1 flex-col items-center justify-end gap-1.5">
                <div className="flex w-full flex-1 items-end">
                  <div className="w-full rounded-t-md transition-all duration-500"
                    style={{ height: height + '%', background: qualityColor(n.quality), opacity: on ? 0.9 : 0.3 }} />
                </div>
                <span className="text-[9px] text-faint">{wd}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Stat label="avg hours" value={rep.avg_hours ? rep.avg_hours + 'h' : '—'} />
        <Stat label="avg quality" value={rep.avg_quality ? rep.avg_quality + '/10' : '—'} />
        <Stat label="nights" value={rep.nights_logged} />
      </div>

      {rep.read && <p className="font-wizard text-[14px] leading-snug text-muted">{rep.read}</p>}
      {rep.mood_insight && <p className="text-[12px] text-faint">{rep.mood_insight}</p>}

      {/* log tonight */}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-3 text-[11px] uppercase tracking-[0.2em] text-faint">log tonight</p>
        <div className="flex items-center gap-3">
          <span className="w-14 text-xs text-faint">hours</span>
          <input type="range" min={0} max={12} step={0.5} value={hours} onChange={(e) => setHours(Number(e.target.value))}
            className="mood-slider flex-1"
            style={{ '--slider-color': 'var(--mood-calm)', '--slider-fill': (hours / 12) * 100 + '%' } as any} />
          <span className="w-10 shrink-0 text-right text-sm text-ink">{hours}h</span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <span className="w-14 text-xs text-faint">quality</span>
          <input type="range" min={1} max={10} step={1} value={quality} onChange={(e) => setQuality(Number(e.target.value))}
            className="mood-slider flex-1"
            style={{ '--slider-color': 'var(--mood-calm)', '--slider-fill': quality * 10 + '%' } as any} />
          <span className="w-10 shrink-0 text-right text-sm text-ink">{quality}/10</span>
        </div>
        <button onClick={() => log('sleep', { hours, quality })}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-full py-2 text-sm font-medium transition-all hover:-translate-y-0.5"
          style={{ background: 'var(--mood-calm)', color: 'var(--bg)' }}>
          <Moon size={16} weight="light" /> Log tonight
        </button>
        <div className="mt-3 flex flex-wrap gap-2">
          {([[7.5, 7, 'a good night'], [6, 4, 'a rough one'], [8, 8, 'slept deeply']] as const).map(([h, q, l]) => (
            <button key={l} onClick={() => log('sleep', { hours: h, quality: q })}
              className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* recent nights — management */}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">recent nights</p>
        {(rep.recent || []).slice().reverse().map((n: any) => (
          <div key={n.date} className="flex items-center justify-between gap-2 border-b border-line/40 py-2 last:border-0">
            <p className="text-sm text-muted">{fmtNight(n.date)} · {n.hours}h · quality {n.quality}/10</p>
            <button onClick={() => log('sleep_delete', { date: n.date })}
              className="text-[11px] text-faint transition-colors hover:text-mood-angry">remove</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function HydrationSection({ onLog }: { onLog: (k: string, p: any) => void }) {
  const [rep, setRep] = useState<any>(null);
  useEffect(() => { getHydrationReport().then(setRep).catch(() => {}); }, []);
  const refresh = async () => { const r = await getHydrationReport().catch(() => null); if (r) setRep(r); };
  const log = async (k: string, p: any) => { await onLog(k, p); await refresh(); };
  if (!rep) return <div className="mt-5 grid h-24 place-items-center text-sm text-faint">listening for water…</div>;
  const goal = rep.goal || 8;
  const today = rep.today || 0;
  return (
    <div className="mt-5 space-y-3">
      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">today</p>
          <p className="font-wizard text-[22px] text-ink">{today}<span className="text-sm text-faint"> / {goal} glasses</span></p>
        </div>
        <div className="mt-4 flex justify-between gap-1">
          {Array.from({ length: goal }, (_, i) => {
            const filled = i < today;
            return (
              <button key={i} onClick={() => log('water_set', { glasses: i + 1 })} title={`${i + 1} glasses`}
                className="grid h-9 flex-1 place-items-center transition-transform hover:-translate-y-0.5">
                <Drop size={22} weight={filled ? 'fill' : 'light'}
                  style={{ color: filled ? 'var(--mood-calm)' : 'var(--line)' }} />
              </button>
            );
          })}
        </div>
        <p className="mt-2 text-[11px] text-faint">tap a droplet to set your water</p>
      </div>

      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week</p>
          <p className="text-xs text-faint">{rep.good_week} watered day{rep.good_week === 1 ? '' : 's'}</p>
        </div>
        <div className="mt-4 flex h-20 items-end justify-between gap-1.5">
          {(rep.week || []).map((w: any) => {
            const on = w.glasses != null;
            const hgt = on ? Math.max(8, ((w.glasses || 0) / goal) * 100) : 4;
            const wd = new Date(w.date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'narrow' });
            return (
              <div key={w.date} className="flex h-full flex-1 flex-col items-center justify-end gap-1.5">
                <div className="flex w-full flex-1 items-end">
                  <div className="w-full rounded-t-md transition-all duration-500"
                    style={{ height: hgt + '%', background: on && (w.glasses || 0) >= goal ? 'var(--sage)' : 'var(--mood-calm)', opacity: on ? 0.9 : 0.3 }} />
                </div>
                <span className="text-[9px] text-faint">{wd}</span>
              </div>
            );
          })}
        </div>
      </div>

      {rep.read && <p className="font-wizard text-[14px] leading-snug text-muted">{rep.read}</p>}

      <div className="flex flex-wrap gap-2">
        <button onClick={() => log('water', { glasses: 1 })}
          className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">+1 glass</button>
        <button onClick={() => log('water', { glasses: 2 })}
          className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">+2 glasses</button>
      </div>
    </div>
  );
}

function NutritionSection({ onLog }: { onLog: (k: string, p: any) => void }) {
  const [rep, setRep] = useState<any>(null);
  const [food, setFood] = useState('');
  const [cal, setCal] = useState('');
  const [meal, setMeal] = useState('lunch');
  useEffect(() => { getNutritionReport().then(setRep).catch(() => {}); }, []);
  const refresh = async () => { const r = await getNutritionReport().catch(() => null); if (r) setRep(r); };
  const log = async (k: string, p: any) => { await onLog(k, p); await refresh(); };
  if (!rep) return <div className="mt-5 grid h-24 place-items-center text-sm text-faint">setting the table…</div>;
  const t = rep.today || {};
  const macroTotal = (t.protein || 0) + (t.carbs || 0) + (t.fat || 0) || 1;
  const macros: [string, number, string][] = [
    ['protein', t.protein || 0, 'var(--sage)'],
    ['carbs', t.carbs || 0, 'var(--lantern)'],
    ['fat', t.fat || 0, 'var(--ember)'],
  ];
  const maxCal = Math.max(2000, ...(rep.week || []).map((w: any) => w.cal || 0));
  return (
    <div className="mt-5 space-y-3">
      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">today's plate</p>
          <p className="font-wizard text-[22px] text-ink">{t.meals || 0}<span className="text-sm text-faint"> meals · {t.cal || 0} kcal</span></p>
        </div>
        <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-line/30">
          {macros.map(([name, v, color]) => (
            <div key={name} className="h-full transition-all duration-500"
              style={{ width: (v / macroTotal) * 100 + '%', background: color }} />
          ))}
        </div>
        <div className="mt-2 flex justify-between text-[10px] text-faint">
          <span>protein {t.protein || 0}g</span><span>carbs {t.carbs || 0}g</span><span>fat {t.fat || 0}g</span>
        </div>
      </div>

      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week</p>
          <p className="text-xs text-faint">avg {rep.avg_cal || 0} kcal / day</p>
        </div>
        <div className="mt-4 flex h-20 items-end justify-between gap-1.5">
          {(rep.week || []).map((w: any) => {
            const on = (w.meals || 0) > 0;
            const hgt = on ? Math.max(8, ((w.cal || 0) / maxCal) * 100) : 4;
            const wd = new Date(w.date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'narrow' });
            return (
              <div key={w.date} className="flex h-full flex-1 flex-col items-center justify-end gap-1.5">
                <div className="flex w-full flex-1 items-end">
                  <div className="w-full rounded-t-md transition-all duration-500"
                    style={{ height: hgt + '%', background: 'var(--lantern)', opacity: on ? 0.9 : 0.3 }} />
                </div>
                <span className="text-[9px] text-faint">{wd}</span>
              </div>
            );
          })}
        </div>
      </div>

      {rep.read && <p className="font-wizard text-[14px] leading-snug text-muted">{rep.read}</p>}

      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">today's meals</p>
        {(rep.recent || []).length === 0 && <p className="text-sm text-faint">nothing yet — the plate is waiting.</p>}
        {(rep.recent || []).map((m: any) => (
          <div key={m._idx} className="flex items-center justify-between gap-2 border-b border-line/40 py-2 last:border-0">
            <p className="flex min-w-0 items-center gap-1.5 text-sm text-muted"><ForkKnife size={14} weight="light" className="shrink-0 text-faint" />{m.food} · {m.calories} kcal · {m.time || ''}</p>
            <button onClick={() => log('nutrition_delete', { index: m._idx })}
              className="text-[11px] text-faint transition-colors hover:text-mood-angry">remove</button>
          </div>
        ))}
      </div>

      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-xs text-faint">log a meal</p>
        <input value={food} onChange={(e) => setFood(e.target.value)} placeholder="what did you eat?"
          className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        <div className="mt-2 flex gap-2">
          <input value={cal} onChange={(e) => setCal(e.target.value)} type="number" placeholder="kcal"
            className="w-24 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
          <select value={meal} onChange={(e) => setMeal(e.target.value)}
            className="flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none focus:border-lantern/60">
            {['breakfast', 'lunch', 'dinner', 'snack'].map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <button onClick={() => { if (food.trim()) { log('nutrition', { food: food.trim(), calories: Number(cal) || 0, meal_time: meal }); setFood(''); setCal(''); } }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2 text-sm font-medium text-bg transition-all hover:bg-ember">
          <Plus size={16} weight="light" /> Add meal
        </button>
        <div className="mt-3 flex flex-wrap gap-2">
          {([[ 'breakfast', 400 ], [ 'lunch', 600 ], [ 'dinner', 600 ]] as const).map(([m, c]) => (
            <button key={m} onClick={() => log('nutrition', { food: m[0].toUpperCase() + m.slice(1), calories: c, meal_time: m })}
              className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
              {m} ~{c}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function WeekBars({ week, value, max, color }: { week: any[]; value: (w: any) => number | null; max: number; color: (v: number) => string }) {
  return (
    <div className="mt-4 flex h-20 items-end justify-between gap-1.5">
      {week.map((w) => {
        const v = value(w);
        const on = v != null && v > 0;
        const hgt = on ? Math.max(8, ((v || 0) / max) * 100) : 4;
        const wd = new Date(w.date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'narrow' });
        return (
          <div key={w.date} className="flex h-full flex-1 flex-col items-center justify-end gap-1.5">
            <div className="flex w-full flex-1 items-end">
              <div className="w-full rounded-t-md transition-all duration-500"
                style={{ height: hgt + '%', background: on ? color(v as number) : 'var(--line)', opacity: on ? 0.9 : 0.3 }} />
            </div>
            <span className="text-[9px] text-faint">{wd}</span>
          </div>
        );
      })}
    </div>
  );
}

function FitnessSection({ onLog }: { onLog: (k: string, p: any) => void }) {
  const [rep, setRep] = useState<any>(null);
  const [type, setType] = useState('');
  const [min, setMin] = useState('');
  useEffect(() => { getFitnessReport().then(setRep).catch(() => {}); }, []);
  const refresh = async () => { const r = await getFitnessReport().catch(() => null); if (r) setRep(r); };
  const log = async (k: string, p: any) => { await onLog(k, p); await refresh(); };
  if (!rep) return <div className="mt-5 grid h-24 place-items-center text-sm text-faint">warming up…</div>;
  const maxMin = Math.max(60, ...(rep.week || []).map((w: any) => w.min || 0));
  return (
    <div className="mt-5 space-y-3">
      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week of movement</p>
          <p className="text-xs text-faint">{rep.active_days} active day{rep.active_days === 1 ? '' : 's'} · {rep.total_min} min</p>
        </div>
        <WeekBars week={rep.week || []} value={(w) => w.min || 0} max={maxMin} color={() => 'var(--ember)'} />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Stat label="active days" value={rep.active_days} />
        <Stat label="minutes" value={rep.total_min} />
        <Stat label="kinds" value={(rep.types || []).length} />
      </div>
      {rep.read && <p className="font-wizard text-[14px] leading-snug text-muted">{rep.read}</p>}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">recent movement</p>
        {(rep.recent || []).length === 0 && <p className="text-sm text-faint">nothing yet — the body is patient.</p>}
        {(rep.recent || []).slice().reverse().map((w: any) => (
          <div key={w._idx} className="flex items-center justify-between gap-2 border-b border-line/40 py-2 last:border-0">
            <p className="flex min-w-0 items-center gap-1.5 text-sm text-muted"><Barbell size={14} weight="light" className="shrink-0 text-faint" />{w.type} · {w.duration} min</p>
            <button onClick={() => log('fitness_delete', { index: w._idx })} className="text-[11px] text-faint transition-colors hover:text-mood-angry">remove</button>
          </div>
        ))}
      </div>
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-xs text-faint">log movement</p>
        <div className="flex gap-2">
          <input value={type} onChange={(e) => setType(e.target.value)} placeholder="what kind? (walk, gym…)"
            className="flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
          <input value={min} onChange={(e) => setMin(e.target.value)} type="number" placeholder="min"
            className="w-20 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        </div>
        <button onClick={() => { if (type.trim()) { log('fitness', { workout_type: type.trim(), duration_min: Number(min) || 0 }); setType(''); setMin(''); } }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2 text-sm font-medium text-bg transition-all hover:bg-ember">
          <Plus size={16} weight="light" /> Add movement
        </button>
        <div className="mt-3 flex flex-wrap gap-2">
          {([['stretch', 10], ['walk', 20], ['gym', 30]] as const).map(([t, m]) => (
            <button key={t} onClick={() => log('fitness', { workout_type: t, duration_min: m })}
              className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">
              {m}-min {t}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function FocusSection({ onLog }: { onLog: (k: string, p: any) => void }) {
  const [rep, setRep] = useState<any>(null);
  const [task, setTask] = useState('');
  const [min, setMin] = useState('25');
  const [timerMin, setTimerMin] = useState<number | null>(null);
  useEffect(() => { getFocusReport().then(setRep).catch(() => {}); }, []);
  const refresh = async () => { const r = await getFocusReport().catch(() => null); if (r) setRep(r); };
  const log = async (k: string, p: any) => { await onLog(k, p); await refresh(); };
  if (!rep) return <div className="mt-5 grid h-24 place-items-center text-sm text-faint">making quiet…</div>;
  const maxMin = Math.max(60, ...(rep.week || []).map((w: any) => w.min || 0));
  return (
    <div className="mt-5 space-y-3">
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">sit into a timer</p>
        <div className="flex flex-wrap gap-2">
          {[20, 25, 50].map((m) => (
            <button key={m} onClick={() => setTimerMin(m)}
              className="rounded-full px-4 py-2 text-xs font-medium transition-all hover:-translate-y-0.5"
              style={{ background: 'color-mix(in srgb, var(--lantern) 18%, transparent)', color: 'var(--lantern)' }}>
              {m}-min quiet
            </button>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-faint">a full-screen countdown; when it ends, a soft bell — and it logs itself.</p>
      </div>

      {timerMin != null && (
        <FocusTimer minutes={timerMin} onClose={() => setTimerMin(null)}
          onComplete={(m) => { log('focus', { task: 'Protected quiet', duration_min: m }); setTimerMin(null); }} />
      )}

      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week of quiet</p>
          <p className="text-xs text-faint">{rep.sessions} session{rep.sessions === 1 ? '' : 's'} · {rep.total_min} min</p>
        </div>
        <WeekBars week={rep.week || []} value={(w) => w.min || 0} max={maxMin} color={() => 'var(--lantern)'} />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Stat label="deep work" value={rep.total_min + 'm'} />
        <Stat label="sessions" value={rep.sessions} />
        <Stat label="avg" value={rep.avg + 'm'} />
      </div>
      {rep.read && <p className="font-wizard text-[14px] leading-snug text-muted">{rep.read}</p>}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">recent sessions</p>
        {(rep.recent || []).length === 0 && <p className="text-sm text-faint">no quiet logged yet.</p>}
        {(rep.recent || []).slice().reverse().map((f: any) => (
          <div key={f._idx} className="flex items-center justify-between gap-2 border-b border-line/40 py-2 last:border-0">
            <p className="flex min-w-0 items-center gap-1.5 text-sm text-muted"><Timer size={14} weight="light" className="shrink-0 text-faint" />{f.task} · {f.duration} min</p>
            <button onClick={() => log('focus_delete', { index: f._idx })} className="text-[11px] text-faint transition-colors hover:text-mood-angry">remove</button>
          </div>
        ))}
      </div>
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-xs text-faint">protect some quiet</p>
        <div className="flex gap-2">
          <input value={task} onChange={(e) => setTask(e.target.value)} placeholder="on what?"
            className="flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
          <input value={min} onChange={(e) => setMin(e.target.value)} type="number" placeholder="min"
            className="w-20 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        </div>
        <button onClick={() => { if (task.trim()) { log('focus', { task: task.trim(), duration_min: Number(min) || 25 }); setTask(''); } }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2 text-sm font-medium text-bg transition-all hover:bg-ember">
          <Plus size={16} weight="light" /> Log focus
        </button>
      </div>
    </div>
  );
}

function stressColor(v: number): string {
  if (v >= 6) return 'var(--ember)';
  if (v >= 4) return 'var(--lantern)';
  return 'var(--sage)';
}
function mindItem(m: any): string {
  if (m.type === 'stress') return `Stress ${m.score}/10${m.trigger ? ' · ' + m.trigger : ''}`;
  if (m.type === 'meditation') return `Stillness · ${m.duration || 0} min`;
  if (m.type === 'gratitude') return `Gratitude: ${(m.items || []).join(', ')}`;
  return m.content || 'Entry';
}

function MentalSection({ onLog }: { onLog: (k: string, p: any) => void }) {
  const [rep, setRep] = useState<any>(null);
  const [score, setScore] = useState(5);
  const [trigger, setTrigger] = useState('');
  const [grat, setGrat] = useState('');
  useEffect(() => { getMentalReport().then(setRep).catch(() => {}); }, []);
  const refresh = async () => { const r = await getMentalReport().catch(() => null); if (r) setRep(r); };
  const log = async (k: string, p: any) => { await onLog(k, p); await refresh(); };
  if (!rep) return <div className="mt-5 grid h-24 place-items-center text-sm text-faint">listening to the mind…</div>;
  return (
    <div className="mt-5 space-y-3">
      <div className="rounded-card border border-line bg-surface p-4">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-[0.2em] text-faint">this week of mind</p>
          <p className="text-xs text-faint">{rep.avg_stress != null ? `avg stress ${rep.avg_stress}/10` : 'no stress logged'}</p>
        </div>
        <WeekBars week={rep.week || []} value={(w) => w.score} max={10} color={stressColor} />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Stat label="avg stress" value={rep.avg_stress != null ? rep.avg_stress + '/10' : '—'} />
        <Stat label="stillness" value={rep.med_sessions} />
        <Stat label="gratitude" value={rep.grat} />
      </div>
      {rep.read && <p className="font-wizard text-[14px] leading-snug text-muted">{rep.read}</p>}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-3 text-[11px] uppercase tracking-[0.2em] text-faint">name the weight</p>
        <div className="flex items-center gap-3">
          <input type="range" min={1} max={10} step={1} value={score} onChange={(e) => setScore(Number(e.target.value))}
            className="mood-slider flex-1" style={{ '--slider-color': stressColor(score), '--slider-fill': score * 10 + '%' } as any} />
          <span className="w-10 shrink-0 text-right text-sm text-ink">{score}/10</span>
        </div>
        <input value={trigger} onChange={(e) => setTrigger(e.target.value)} placeholder="what's pressing? (optional)"
          className="mt-3 w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        <button onClick={() => { log('stress', { score, trigger: trigger.trim() }); setTrigger(''); }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full py-2 text-sm font-medium transition-all hover:-translate-y-0.5"
          style={{ background: 'color-mix(in srgb, var(--ember) 25%, transparent)', color: 'var(--ember)' }}>
          <Brain size={16} weight="light" /> Log stress
        </button>
      </div>
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">and the light</p>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => log('meditation', { duration_min: 10 })}
            className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition-all hover:-translate-y-0.5 hover:border-lantern/50 hover:text-lantern">10-min stillness</button>
        </div>
        <div className="mt-3 flex gap-2">
          <input value={grat} onChange={(e) => setGrat(e.target.value)} placeholder="one good thing…"
            className="min-w-0 flex-1 rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
          <button onClick={() => { if (grat.trim()) { log('gratitude', { items: [grat.trim()] }); setGrat(''); } }}
            className="shrink-0 rounded-full px-3 py-1.5 text-xs font-medium"
            style={{ background: 'color-mix(in srgb, var(--sage) 20%, transparent)', color: 'var(--sage)' }}>
            keep it
          </button>
        </div>
      </div>
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-faint">recent mind</p>
        {(rep.recent || []).length === 0 && <p className="text-sm text-faint">a quiet page.</p>}
        {(rep.recent || []).slice().reverse().map((m: any) => (
          <div key={m._idx} className="flex items-center justify-between gap-2 border-b border-line/40 py-2 last:border-0">
            <p className="min-w-0 truncate text-sm text-muted">{mindItem(m)}</p>
            <button onClick={() => log('mental_delete', { index: m._idx })} className="text-[11px] text-faint transition-colors hover:text-mood-angry">remove</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function GenericSection({ model, records, onLog }: { model: DimModel; records: any; onLog: (k: string, p: any) => void }) {
  const items = records?.items || [];
  const [form, setForm] = useState<any>({});
  return (
    <div className="mt-5 space-y-3">
      <p className="text-[11px] uppercase tracking-[0.2em] text-faint">Recent</p>
      {items.length === 0 && <p className="text-sm text-faint">Nothing logged yet.</p>}
      {items.slice().reverse().map((it: any, i: number) => (
        <div key={i} className="rounded-card border border-line bg-surface px-4 py-3 text-sm text-muted">
          {describeItem(model.id, it)}
        </div>
      ))}
      <div className="rounded-card border border-line bg-surface p-4">
        <p className="mb-1 text-xs text-faint">Log one now</p>
        {model.fields.map((f) => (
          <input key={f.key} type={f.type === 'number' ? 'number' : 'text'} placeholder={f.placeholder}
            value={form[f.key] ?? ''} onChange={(e) => setForm((p: any) => ({ ...p, [f.key]: e.target.value }))}
            className="mt-2 w-full rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink outline-none placeholder:text-faint focus:border-lantern/60" />
        ))}
        <button onClick={() => { onLog(model.logKind, form); setForm({}); }}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-lantern py-2 text-sm font-medium text-bg transition-all hover:bg-ember">
          <Plus size={16} weight="light" /> Add
        </button>
      </div>
    </div>
  );
}

function describeItem(dim: string, it: any): string {
  if (dim === 'nutrition') return `${it.food || 'Meal'} · ${it.calories || 0} kcal · ${it.time || ''}`;
  if (dim === 'fitness') return `${it.type || 'Workout'} · ${it.duration || 0} min`;
  if (dim === 'focus') return `${it.task || 'Focus'} · ${it.duration || 0} min`;
  if (dim === 'mental') {
    if (it.type === 'stress') return `Stress ${it.score}/10${it.trigger ? ' · ' + it.trigger : ''}`;
    if (it.type === 'meditation') return `Meditation · ${it.duration || 0} min`;
    if (it.items) return `Gratitude: ${it.items.join(', ')}`;
    return 'Entry';
  }
  if (dim === 'hydration') return `${it.glasses || 0} glasses · ${it.time || ''}`;
  if (dim === 'sleep') return `${it.hours || 0}h · quality ${it.quality ?? '-'}/10`;
  return it.content || 'Entry';
}
