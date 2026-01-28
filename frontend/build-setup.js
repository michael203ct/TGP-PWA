const fs = require('fs');
const path = require('path');

console.log('Running build setup...');

const distDir = path.join(__dirname, 'dist');

// Check if dist directory exists
if (!fs.existsSync(distDir)) {
    console.log('dist directory not found - skipping build setup');
    process.exit(0);
}

// Try to find and copy Ionicons font to root of dist
const fontSourcePath = path.join(distDir, 'assets/node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/Fonts');
const ioniconsDestPath = path.join(distDir, 'ionicons.ttf');

// Check if ionicons.ttf already exists at root
if (fs.existsSync(ioniconsDestPath)) {
    console.log('ionicons.ttf already exists at root - skipping font copy');
} else if (fs.existsSync(fontSourcePath)) {
    // Font source exists, copy it
    try {
        const fontFiles = fs.readdirSync(fontSourcePath).filter(f => f.startsWith('Ionicons'));
        if (fontFiles.length > 0) {
            const fontFile = fontFiles[0];
            const sourcePath = path.join(fontSourcePath, fontFile);
            fs.copyFileSync(sourcePath, ioniconsDestPath);
            console.log(`Copied ${fontFile} to ionicons.ttf`);
            
            // Update all HTML and JS files to use the new font path
            const oldPath = `/assets/node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/Fonts/${fontFile}`;
            const newPath = '/ionicons.ttf';
            
            updateFilesRecursively(distDir, oldPath, newPath);
        }
    } catch (err) {
        console.log('Font copy skipped:', err.message);
    }
} else {
    console.log('Font source path not found - ionicons.ttf should already be in place');
}

function updateFilesRecursively(dir, oldPath, newPath) {
    try {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            
            if (stat.isDirectory()) {
                updateFilesRecursively(filePath, oldPath, newPath);
            } else if (file.endsWith('.html') || file.endsWith('.js')) {
                let content = fs.readFileSync(filePath, 'utf8');
                if (content.includes(oldPath)) {
                    content = content.replace(new RegExp(oldPath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), newPath);
                    fs.writeFileSync(filePath, content);
                    console.log(`Updated font path in: ${file}`);
                }
            }
        }
    } catch (err) {
        // Ignore errors in recursive update
    }
}

// Add meta tags and font-face to HTML files
const metaTags = `<title>The Gig Pulse | Educate. Elevate. Motivate.</title>
<meta name="description" content="Your go-to resource for gig economy workers. Curated videos, news, driver essentials, and helpful tools for Uber, Lyft, DoorDash, Instacart drivers."/>
<meta property="og:title" content="The Gig Pulse | Educate. Elevate. Motivate."/>
<meta property="og:description" content="Your go-to resource for gig economy workers. Curated videos, news, driver essentials, and helpful tools."/>
<meta property="og:image" content="https://thegigpulse.com/og-image.png"/>
<meta property="og:url" content="https://thegigpulse.com"/>
<meta property="og:type" content="website"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:image" content="https://thegigpulse.com/og-image.png"/>
<meta name="theme-color" content="#00D9FF"/>
<link rel="icon" type="image/png" href="/logo.png"/>
<link rel="apple-touch-icon" href="/logo.png"/>
<link rel="manifest" href="/manifest.json"/>`;

const fontFace = `@font-face{font-family:'Ionicons';src:url('/ionicons.ttf') format('truetype');font-weight:normal;font-style:normal;font-display:block;}`;

function addMetaAndFontFace(dir) {
    try {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            
            if (stat.isDirectory()) {
                addMetaAndFontFace(filePath);
            } else if (file.endsWith('.html')) {
                let content = fs.readFileSync(filePath, 'utf8');
                let modified = false;
                
                // Remove empty title tag
                if (content.includes('<title data-rh="true"></title>')) {
                    content = content.replace('<title data-rh="true"></title>', '');
                    modified = true;
                }
                
                // Add meta tags after <head>
                if (content.includes('<head>') && !content.includes('og:title')) {
                    content = content.replace('<head>', `<head>${metaTags}`);
                    modified = true;
                }
                
                // Add font-face in stylesheet
                if (content.includes('[stylesheet-group="0"]{}') && !content.includes("font-family:'Ionicons'")) {
                    content = content.replace('[stylesheet-group="0"]{}', `[stylesheet-group="0"]{}${fontFace}`);
                    modified = true;
                }
                
                if (modified) {
                    fs.writeFileSync(filePath, content);
                    console.log(`Updated meta/font in: ${file}`);
                }
            }
        }
    } catch (err) {
        // Ignore errors
    }
}

addMetaAndFontFace(distDir);

// Ensure logo.png exists (copy from assets if needed)
const logoDestPath = path.join(distDir, 'logo.png');
if (!fs.existsSync(logoDestPath)) {
    const logoSource = path.join(distDir, 'assets/assets');
    if (fs.existsSync(logoSource)) {
        try {
            const logoFiles = fs.readdirSync(logoSource).filter(f => f.startsWith('logo-full'));
            if (logoFiles.length > 0) {
                fs.copyFileSync(path.join(logoSource, logoFiles[0]), logoDestPath);
                console.log('Copied logo.png');
            }
        } catch (err) {
            console.log('Logo copy skipped:', err.message);
        }
    }
}

console.log('Build setup complete!');
