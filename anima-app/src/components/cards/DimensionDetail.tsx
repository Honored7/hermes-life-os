import { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Wind, ChatTeardrop, Plus, Fire, Check } from '@phosphor-icons/react';
import type { DimConfig } from '../../lib/dimensions';
import type { DimModel } from '../../lib/lifeModel';

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

        {isGoals && <GoalsSection records={records} onLog={onLog} />}
        {isHabits && <HabitsSection records={records} onLog={onLog} />}
        {!isGoals && !isHabits && <GenericSection model={model} records={records} onLog={onLog} />}

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
