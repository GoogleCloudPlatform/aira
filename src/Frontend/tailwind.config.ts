import type { Config } from "tailwindcss";

const getTheme = () => {
    switch(process.env.NEXT_PUBLIC_DEFAULT_THEME) {
        case "SABER":
            return { 
                border: `#CED4DA`,
                input: `#CED4DA`,
                ring: `#212529`,
                background: `#FFFFFF`,
                foreground: `#212529`,
                primary: {
                    DEFAULT: `#00B041`,
                    foreground: `#50A000`,
                },
                secondary: {
                    DEFAULT: `#f1f5f9`,
                    foreground: `#29332D`,
                },
                destructive: {
                    DEFAULT: `#BC3206`, 
                    foreground: `#CED4DA`,
                },
                muted: {
                    DEFAULT: `#CED4DA`, 
                    foreground: `#8E9098`,
                },
                accent: {
                    DEFAULT: `#CED4DA`,
                    foreground: `#29332D`,
                },
                popover: {
                    DEFAULT: `#FFFFFF`,
                    foreground: `#212529`,
                },
                card: {
                    DEFAULT: `#FFFFFF`,
                    foreground: `#212529`,
                },
                darkBorder: `#2A2A2A`,
                darkInput: `#2A2A2A`,
                darkRing: `#212529`, 
                darkBackground: `#212529`, 
                darkForeground: `#CED4DA`,
                darkPrimary: {
                    DEFAULT: `#29332D`,
                    foreground: `#38473E`,
                },
                darkSecondary: {
                    DEFAULT: `#2A2A2A`, 
                    foreground: `#CED4DA`
                },
                darkDestructive: {
                    DEFAULT: `#BC3206`, 
                    foreground: `#CED4DA`
                },
                darkMuted: {
                    DEFAULT: `#2A2A2A`,
                    foreground: `#8E9098`,
                },
                darkAccent: {
                    DEFAULT: `#2A2A2A`,
                    foreground: `#CED4DA`
                },
                darkPopover: {
                    DEFAULT: `#212529`, 
                    foreground: `#CED4DA`
                },
                darkCard: {
                    DEFAULT: `#212529`, 
                    foreground: `#CED4DA`
                },
            }
        case 'LIA': return {
            border: "#e2e8f0",
            input: "#e2e8f0",
            ring: "#010816",
            background: "#ffffff",
            foreground: "#010816",
            primary: {
                DEFAULT: "#2362ea",
                foreground: "#4479ed",
            },
            secondary: {
                DEFAULT: "#f1f5f9",
                foreground: "#0f172a",
            },
            destructive: {
                DEFAULT: "#ee4444",
                foreground: "#f7f9fb",
            },
            muted: {
                DEFAULT: "#f1f5f9",
                foreground: "#64748b",
            },
            accent: {
                DEFAULT: "#f1f5f9",
                foreground: "#0f172a",
            },
            popover: {
                DEFAULT: "#ffffff",
                foreground: "#010816",
            },
            card: {
                DEFAULT: "#ffffff",
                foreground: "#010816",
            },
            darkBorder: "#1e293b",
            darkInput: "#1e293b",
            darkRing: "#020817",
            darkBackground: "#020817",
            darkForeground: "#f7f9fb",
            darkPrimary: {
                DEFAULT: "#162350",
                foreground: "#203578",
            },
            darkSecondary: {
                DEFAULT: "#1e293b",
                foreground: "#f7f9fb",
            },
            darkDestructive: {
                DEFAULT: "#ee4444",
                foreground: "#f7f9fb",
            },
            darkMuted: {
                DEFAULT: "#1e293b",
                foreground: "#94a3b7",
            },
            darkAccent: {
                DEFAULT: "#1e293b",
                foreground: "#f7f9fb",
            },
            darkPopover: {
                DEFAULT: "#020817",
                foreground: "#f7f9fb",
            },
            darkCard: {
                DEFAULT: "#020817",
                foreground: "#f7f9fb",
            },
        } 
        default:
            return { border: `hsl(214.3, 31.8%, 91.4%)`,
                input: `hsl(214.3, 31.8%, 91.4%)`,
                ring: `hsl(222.2, 84%, 4.9%)`,
                background: `#FFFFFF`,
                foreground: `hsl(222.2, 84%, 4.9%)`,
                primary: {
                    DEFAULT: `hsl(221, 83%, 53%)`,
                    foreground: `hsl(221, 83%, 60%)`,
                },
                secondary: {
                    DEFAULT: `hsl(210, 40%, 96.1%)`,
                    foreground: `hsl(222.2, 47.4%, 11.2%)`,
                },
                destructive: {
                    DEFAULT: `hsl(0, 84.2%, 60.2%)`,
                    foreground: `hsl(210, 40%, 98%)`,
                },
                muted: {
                    DEFAULT: `hsl(210, 40%, 96.1%)`,
                    foreground: `hsl(215.4, 16.3%, 46.9%)`,
                },
                accent: {
                    DEFAULT: `hsl(210, 40%, 96.1%)`,
                    foreground: `hsl(222.2, 47.4%, 11.2%)`,
                },
                popover: {
                    DEFAULT: `#FFFFFF`,
                    foreground: `hsl(222.2, 84%, 4.9%)`,
                },
                card: {
                    DEFAULT: `#FFFFFF`,
                    foreground: `hsl(222.2, 84%, 4.9%)`,
                },
                darkBorder: `hsl(217.2, 32.6%, 17.5%)`,
                darkInput: `hsl(217.2, 32.6%, 17.5%)`,
                darkRing: `hsl(222.2, 84%, 4.9%)`,
                darkBackground: `hsl(222.2, 84%, 4.9%)`,
                darkForeground: `hsl(210, 40%, 98%)`,
                darkPrimary: {
                    DEFAULT: `hsl(226, 57%, 20%)`,
                    foreground: `hsl(226, 57%, 30%)`,
                },
                darkSecondary: {
                    DEFAULT: `hsl(217.2, 32.6%, 17.5%)`,
                    foreground: `hsl(210, 40%, 98%)`,
                },
                darkDestructive: {
                    DEFAULT: `hsl(0, 84.2%, 60.2%)`,
                    foreground: `hsl(210, 40%, 98%)`,
                },
                darkMuted: {
                    DEFAULT: `hsl(217.2, 32.6%, 17.5%)`,
                    foreground: `hsl(215, 20.2%, 65.1%)`,
                },
                darkAccent: {
                    DEFAULT: `hsl(217.2, 32.6%, 17.5%)`,
                    foreground: `hsl(210, 40%, 98%)`,
                },
                darkPopover: {
                    DEFAULT: `hsl(222.2, 84%, 4.9%)`,
                    foreground: `hsl(210, 40%, 98%)`,
                },
                darkCard: {
                    DEFAULT: `hsl(222.2, 84%, 4.9%)`,
                    foreground: `hsl(210, 40%, 98%)`,
                }, }
    }
}

const colors = getTheme()

const config: Config = {
    darkMode: ["class"],
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/forms/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/hooks/*.{js,ts,jsx,tsx,mdx}",
    ],
    prefix: "",
    theme: {
        container: {
            center: true,
            padding: "2rem",
            screens: {
                "2xl": "1400px",
            },
        },
        extend: {
            colors: {
                border: colors.border,
                input: colors.input,
                ring: colors.ring,
                background: colors.background,
                foreground: colors.foreground,
                primary: {
                    DEFAULT: colors.primary.DEFAULT,
                    foreground: colors.primary.foreground,
                },
                secondary: {
                    DEFAULT: colors.secondary.DEFAULT,
                    foreground: colors.secondary.foreground,
                },
                destructive: {
                    DEFAULT: colors.destructive.DEFAULT,
                    foreground: colors.destructive.foreground,
                },
                muted: {
                    DEFAULT: colors.muted.DEFAULT,
                    foreground: colors.muted.foreground,
                },
                accent: {
                    DEFAULT: colors.accent.DEFAULT,
                    foreground: colors.accent.foreground,
                },
                popover: {
                    DEFAULT: colors.popover.DEFAULT,
                    foreground: colors.popover.foreground,
                },
                card: {
                    DEFAULT: colors.card.DEFAULT,
                    foreground: colors.card.foreground,
                },
                darkBorder: colors.darkBorder,
                darkInput: colors.darkInput,
                darkRing: colors.darkRing,
                darkBackground: colors.darkBackground,
                darkForeground: colors.darkForeground,
                darkPrimary: {
                    DEFAULT: colors.darkPrimary.DEFAULT,
                    foreground: colors.darkPrimary.foreground,
                },
                darkSecondary: {
                    DEFAULT: colors.darkSecondary.DEFAULT,
                    foreground: colors.darkSecondary.foreground,
                },
                darkDestructive: {
                    DEFAULT: colors.darkDestructive.DEFAULT,
                    foreground: colors.darkDestructive.foreground,
                },
                darkMuted: {
                    DEFAULT: colors.darkMuted.DEFAULT,
                    foreground: colors.darkMuted.foreground,
                },
                darkAccent: {
                    DEFAULT: colors.darkAccent.DEFAULT,
                    foreground: colors.darkAccent.foreground,
                },
                darkPopover: {
                    DEFAULT: colors.darkPopover.DEFAULT,
                    foreground: colors.darkPopover.foreground,
                },
                darkCard: {
                    DEFAULT: colors.darkCard.DEFAULT,
                    foreground: colors.darkCard.foreground,
                },
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
            },
            keyframes: {
                "accordion-down": {
                    from: { height: "0" },
                    to: { height: "var(--radix-accordion-content-height)" },
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: "0" },
                },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [require("tailwindcss-animate")],
};
export default config;
