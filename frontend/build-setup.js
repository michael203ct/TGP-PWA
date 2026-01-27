const fs = require('fs');
const path = require('path');

console.log('Running build setup...');

const distDir = path.join(__dirname, 'dist');

// Find and copy Ionicons font to root of dist
const fontSourcePath = path.join(distDir, 'assets/node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/Fonts');
const fontFiles = fs.readdirSync(fontSourcePath).filter(f => f.startsWith('Ionicons'));

if (fontFiles.length > 0) {
    const fontFile = fontFiles[0];
    const sourcePath = path.join(fontSourcePath, fontFile);
    const destPath = path.join(distDir, 'ionicons.ttf');
    
    fs.copyFileSync(sourcePath, destPath);
    console.log(`Copied ${fontFile} to ionicons.ttf`);
    
    // Update all HTML files to use the new font path
    const oldPath = `/assets/node_modules/@expo/vector-icons/build/vendor/react-native-vector-icons/Fonts/${fontFile}`;
    const newPath = '/ionicons.ttf';
    
    function updateFiles(dir) {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            
            if (stat.isDirectory()) {
                updateFiles(filePath);
            } else if (file.endsWith('.html') || file.endsWith('.js')) {
                let content = fs.readFileSync(filePath, 'utf8');
                if (content.includes(oldPath)) {
                    content = content.replace(new RegExp(oldPath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), newPath);
                    fs.writeFileSync(filePath, content);
                    console.log(`Updated font path in: ${filePath}`);
                }
            }
        }
    }
    
    updateFiles(distDir);
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
<link rel="icon" type="image/png" href="/logo.png"/>`;

const fontFace = `@font-face{font-family:'Ionicons';src:url('/ionicons.ttf') format('truetype');font-weight:normal;font-style:normal;font-display:block;}`;

function addMetaAndFontFace(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
            addMetaAndFontFace(filePath);
        } else if (file.endsWith('.html')) {
            let content = fs.readFileSync(filePath, 'utf8');
            
            // Remove empty title tag
            content = content.replace('<title data-rh="true"></title>', '');
            
            // Add meta tags after <head>
            if (content.includes('<head>') && !content.includes('og:title')) {
                content = content.replace('<head>', `<head>${metaTags}`);
            }
            
            // Add font-face in stylesheet
            if (content.includes('[stylesheet-group="0"]{}') && !content.includes("font-family:'Ionicons'")) {
                content = content.replace('[stylesheet-group="0"]{}', `[stylesheet-group="0"]{}${fontFace}`);
            }
            
            fs.writeFileSync(filePath, content);
        }
    }
}

addMetaAndFontFace(distDir);

// Ensure logo.png exists (copy from assets if needed)
const logoSource = path.join(distDir, 'assets/assets');
if (fs.existsSync(logoSource)) {
    const logoFiles = fs.readdirSync(logoSource).filter(f => f.startsWith('logo-full'));
    if (logoFiles.length > 0 && !fs.existsSync(path.join(distDir, 'logo.png'))) {
        fs.copyFileSync(path.join(logoSource, logoFiles[0]), path.join(distDir, 'logo.png'));
        console.log('Copied logo.png');
    }
}

console.log('Build setup complete!');
