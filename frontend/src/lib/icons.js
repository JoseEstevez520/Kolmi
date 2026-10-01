import { defineComponent, h, markRaw } from 'vue'
import {
  Atom,
  Award,
  Beaker,
  Book,
  BookMarked,
  BookOpen,
  Bot,
  Boxes,
  Brain,
  Briefcase,
  Building2,
  Calculator,
  Calendar,
  Camera,
  CircleDot,
  ClipboardList,
  Code,
  Coffee,
  Compass,
  Cpu,
  Database,
  Dumbbell,
  Feather,
  FileCode,
  FileStack,
  FileText,
  Flag,
  FlaskConical,
  Folder,
  FolderOpen,
  FolderTree,
  Gamepad2,
  GitBranch,
  Globe,
  GraduationCap,
  Grid3x3,
  Heart,
  Home,
  Landmark,
  Languages,
  Layers,
  LayoutGrid,
  Library,
  Lightbulb,
  Link,
  List,
  ListChecks,
  Map,
  Mic,
  Milestone,
  Music,
  Network,
  Notebook,
  NotebookPen,
  Palette,
  PenTool,
  Plane,
  Puzzle,
  Rocket,
  Route,
  Scale,
  School,
  ScrollText,
  Settings,
  Shield,
  Sigma,
  Sparkles,
  SquareStack,
  Star,
  Stethoscope,
  Tag,
  Target,
  Terminal,
  TreePine,
  Trophy,
  University,
  Users,
  Video,
  Wallet,
  Wrench,
  Zap,
} from '@lucide/vue'

// The icons an admin can pick for a node. The database stores the name; the app
// turns it back into a component (iconByName). Keeping the list closed means a
// name that is no longer known can never break a render.
export const ICONS = {
  Atom,
  Award,
  Beaker,
  Book,
  BookMarked,
  BookOpen,
  Bot,
  Boxes,
  Brain,
  Briefcase,
  Building2,
  Calculator,
  Calendar,
  Camera,
  CircleDot,
  ClipboardList,
  Code,
  Coffee,
  Compass,
  Cpu,
  Database,
  Dumbbell,
  Feather,
  FileCode,
  FileStack,
  FileText,
  Flag,
  FlaskConical,
  Folder,
  FolderOpen,
  FolderTree,
  Gamepad2,
  GitBranch,
  Globe,
  GraduationCap,
  Grid3x3,
  Heart,
  Home,
  Landmark,
  Languages,
  Layers,
  LayoutGrid,
  Library,
  Lightbulb,
  Link,
  List,
  ListChecks,
  Map,
  Mic,
  Milestone,
  Music,
  Network,
  Notebook,
  NotebookPen,
  Palette,
  PenTool,
  Plane,
  Puzzle,
  Rocket,
  Route,
  Scale,
  School,
  ScrollText,
  Settings,
  Shield,
  Sigma,
  Sparkles,
  SquareStack,
  Star,
  Stethoscope,
  Tag,
  Target,
  Terminal,
  TreePine,
  Trophy,
  University,
  Users,
  Video,
  Wallet,
  Wrench,
  Zap,
}

export const ICON_NAMES = Object.keys(ICONS).sort()

// A node's colour is a plain string. Empty means the app's grey, so colour is
// only there when it tells sections apart (design.md, "Colour").
export const NODE_COLORS = [
  { name: 'Grey', value: '' },
  { name: 'Blue', value: '#2563eb' },
  { name: 'Teal', value: '#0d9488' },
  { name: 'Violet', value: '#7c3aed' },
  { name: 'Amber', value: '#d97706' },
  { name: 'Fuchsia', value: '#c026d3' },
  { name: 'Lime', value: '#65a30d' },
  { name: 'Rose', value: '#e11d48' },
]

export function iconByName(name) {
  return (name && ICONS[name]) || null
}

// NavTree and the cards ask for the icon as a component, not already painted, so
// a node's colour has to travel inside a component of its own. They are cached,
// so a new one is not built on every render.
const colored = new WeakMap()

function coloredIcon(icon, color) {
  // A plain object keyed by colour, not a Map: this file imports Lucide's `Map`
  // icon, which would shadow the global Map constructor.
  if (!colored.has(icon)) colored.set(icon, Object.create(null))
  const byColor = colored.get(icon)
  if (!(color in byColor)) {
    byColor[color] = markRaw(
      defineComponent({
        name: 'NodeIcon',
        inheritAttrs: false,
        setup:
          (_, { attrs }) =>
          () =>
            h(icon, { ...attrs, style: { color } }),
      }),
    )
  }
  return byColor[color]
}

// The component to hand to `:icon`, with the node's colour on it.
export function nodeIcon(node) {
  const icon = iconByName(node?.icon)
  if (!icon) return null
  return coloredIcon(icon, node?.color || 'var(--color-fg)')
}
