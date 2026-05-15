// src/components/Icons.jsx

/**
 * MwalimuLogo — The official Mwalimu AI three-leaf pinwheel logo.
 * Used everywhere Mwalimu branding is needed (sidebar, tutor header, chat bubbles, etc.)
 */
export function MwalimuLogo({ size = 32, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Mwalimu AI logo"
      className={className}
    >
      <defs>
        {/* Outer ring: blue → brown */}
        <linearGradient id="ml-ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#29ABE2" />
          <stop offset="50%"  stopColor="#1A7BB8" />
          <stop offset="100%" stopColor="#8B5E3C" />
        </linearGradient>
        {/* Leaf 1 – dark green */}
        <linearGradient id="ml-leaf1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#1B6B3A" />
          <stop offset="100%" stopColor="#2E8B57" />
        </linearGradient>
        {/* Leaf 2 – medium green */}
        <linearGradient id="ml-leaf2" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%"   stopColor="#4CAF50" />
          <stop offset="100%" stopColor="#81C784" />
        </linearGradient>
        {/* Leaf 3 – lime / yellow-green */}
        <linearGradient id="ml-leaf3" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%"   stopColor="#8BC34A" />
          <stop offset="100%" stopColor="#C5E17A" />
        </linearGradient>
        {/* Shared specular highlight per leaf */}
        <radialGradient id="ml-shine" cx="30%" cy="30%" r="60%">
          <stop offset="0%"   stopColor="rgba(255,255,255,0.35)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0)" />
        </radialGradient>
      </defs>

      {/* Outer ring */}
      <circle cx="100" cy="100" r="98" fill="url(#ml-ringGrad)" />
      {/* White inner disc (ring gap) */}
      <circle cx="100" cy="100" r="82" fill="white" />

      {/* Leaf 1 (dark green) */}
      <g transform="rotate(0 100 100)">
        <path d="M100 100 C68 62,38 52,42 92 C44 115,72 128,96 108 Z" fill="url(#ml-leaf1)" />
        <path d="M100 100 C68 62,38 52,42 92 C44 115,72 128,96 108 Z" fill="url(#ml-shine)" />
      </g>

      {/* Leaf 2 (medium green) */}
      <g transform="rotate(120 100 100)">
        <path d="M100 100 C68 62,38 52,42 92 C44 115,72 128,96 108 Z" fill="url(#ml-leaf2)" />
        <path d="M100 100 C68 62,38 52,42 92 C44 115,72 128,96 108 Z" fill="url(#ml-shine)" />
      </g>

      {/* Leaf 3 (lime green) */}
      <g transform="rotate(240 100 100)">
        <path d="M100 100 C68 62,38 52,42 92 C44 115,72 128,96 108 Z" fill="url(#ml-leaf3)" />
        <path d="M100 100 C68 62,38 52,42 92 C44 115,72 128,96 108 Z" fill="url(#ml-shine)" />
      </g>

      {/* Central hub */}
      <circle cx="100" cy="100" r="7" fill="#1B5E20" opacity="0.6" />
    </svg>
  );
}

/**
 * CBCLogo — Alias to MwalimuLogo for backward-compatibility.
 * Used in the sidebar and topbar as the app brand logo.
 */
export function CBCLogo({ size = 32, className = "" }) {
  return <MwalimuLogo size={size} className={className} />;
}
import {
  LayoutGrid, BookOpen, Library, Bot, MessageSquare, LogOut, 
  Menu, User, Users, Search, ChevronDown, SquarePen, PanelLeft,
  Gamepad2, Rocket, FlaskConical, Settings, CreditCard, Award, BarChart3, Coins
} from "lucide-react";

export function IconSimulate({ size = 18, className = "", ...props }) { return <Gamepad2 size={size} className={className} {...props} />; }
export function IconProject({ size = 18, className = "", ...props }) { return <Rocket size={size} className={className} {...props} />; }
export function IconExperiment({ size = 18, className = "", ...props }) { return <FlaskConical size={size} className={className} {...props} />; }
export function IconSettings({ size = 18, className = "", ...props }) { return <Settings size={size} className={className} {...props} />; }

export function IconGrid({ size = 18, className = "", ...props }) { return <LayoutGrid size={size} className={className} {...props} />; }
export function IconBook({ size = 18, className = "", ...props }) { return <BookOpen size={size} className={className} {...props} />; }
export function IconLibrary({ size = 18, className = "", ...props }) { return <Library size={size} className={className} {...props} />; }
export function IconBot({ size = 18, className = "", ...props }) { return <Bot size={size} className={className} {...props} />; }
export function IconFeed({ size = 18, className = "", ...props }) { return <MessageSquare size={size} className={className} {...props} />; }
export function IconLogout({ size = 18, className = "", ...props }) { return <LogOut size={size} className={className} {...props} />; }
export function IconMenu({ size = 18, className = "", ...props }) { return <Menu size={size} className={className} {...props} />; }
export function IconUser({ size = 18, className = "", ...props }) { return <User size={size} className={className} {...props} />; }
export function IconChat({ size = 18, className = "", ...props }) { return <MessageSquare size={size} className={className} {...props} />; }
export function IconSearch({ size = 18, className = "", ...props }) { return <Search size={size} className={className} {...props} />; }
export function IconChevronDown({ size = 18, className = "", ...props }) { return <ChevronDown size={size} className={className} {...props} />; }
export function IconCompose({ size = 18, className = "", ...props }) { return <SquarePen size={size} className={className} {...props} />; }
export function IconPanel({ size = 18, className = "", ...props }) { return <PanelLeft size={size} className={className} {...props} />; }
export function IconCollaborate({ size = 18, className = "", ...props }) { return <Users size={size} className={className} {...props} />; }
export function IconBilling({ size = 18, className = "", ...props }) { return <CreditCard size={size} className={className} {...props} />; }
export function IconCompetency({ size = 18, className = "", ...props }) { return <Award size={size} className={className} {...props} />; }
export function IconUsage({ size = 18, className = "", ...props }) { return <BarChart3 size={size} className={className} {...props} />; }
export function IconTokens({ size = 18, className = "", ...props }) { return <Coins size={size} className={className} {...props} />; }
