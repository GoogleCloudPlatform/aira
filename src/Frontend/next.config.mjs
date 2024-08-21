import { fileURLToPath } from 'url';
import path, { dirname } from "path";
import createNextIntlPlugin from 'next-intl/plugin';
 
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const withNextIntl = createNextIntlPlugin();
 
/** @type {import('next').NextConfig} */
const nextConfig = {
    webpack: (config, { isServer }) => {
        config.resolve.alias['@'] = path.join(__dirname, 'src');
        return config;
    },
    transpilePackages: ['lucide-react'], 
};
 
export default withNextIntl(nextConfig);