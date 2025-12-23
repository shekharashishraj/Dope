#!/usr/bin/env node
/**
 * Audit visibility of hidden text attacks using Playwright.
 * Checks if tokens exist in DOM text but not in visible text.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Setup logging to file with timestamp.
 */
function setupLogging(logDir = 'logs') {
    if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
    }
    
    const timestamp = new Date().toISOString()
        .replace(/:/g, '-')
        .replace(/\..+/, '')
        .replace('T', '_');
    const logFile = path.join(logDir, `04_audit_${timestamp}.log`);
    
    const logStream = fs.createWriteStream(logFile, { flags: 'a' });
    
    function log(level, message) {
        const timestamp = new Date().toISOString();
        const logMessage = `${timestamp} - ${level} - ${message}`;
        console.log(logMessage);
        logStream.write(logMessage + '\n');
    }
    
    return {
        info: (msg) => log('INFO', msg),
        warn: (msg) => log('WARN', msg),
        error: (msg) => log('ERROR', msg),
        debug: (msg) => log('DEBUG', msg),
        close: () => logStream.end()
    };
}

/**
 * Extract visible text from element using computed styles and bounding box.
 */
async function extractVisibleText(element) {
    const visibleTexts = [];
    
    async function traverse(node) {
        if (!node) return;
        
        const tagName = await node.evaluate(el => el.tagName);
        if (tagName === 'SCRIPT' || tagName === 'STYLE') {
            return;
        }
        
        // Check computed style
        const style = await node.evaluate(el => {
            const computed = window.getComputedStyle(el);
            return {
                display: computed.display,
                visibility: computed.visibility,
                opacity: computed.opacity,
                position: computed.position,
                clip: computed.clip,
                clipPath: computed.clipPath,
                width: computed.width,
                height: computed.height,
                fontSize: computed.fontSize
            };
        });
        
        // Check if element is visible
        const isVisible = style.display !== 'none' &&
                         style.visibility !== 'hidden' &&
                         parseFloat(style.opacity) > 0 &&
                         style.width !== '0px' &&
                         style.height !== '0px';
        
        if (!isVisible) {
            return;
        }
        
        // Get bounding box
        const box = await node.boundingBox();
        if (!box || box.width === 0 || box.height === 0) {
            return;
        }
        
        // Get text content
        const text = await node.textContent();
        if (text && text.trim()) {
            visibleTexts.push(text.trim());
        }
        
        // Traverse children
        const children = await node.$$(':scope > *');
        for (const child of children) {
            await traverse(child);
        }
    }
    
    await traverse(element);
    return visibleTexts.join(' ');
}

/**
 * Audit a single HTML file.
 */
async function auditFile(page, filePath, logger) {
    const startTime = Date.now();
    logger.info(`Auditing file: ${filePath}`);
    
    try {
        // Load page
        await page.goto(`file://${filePath}`);
        await page.waitForLoadState('networkidle');
        
        // Extract DOM text (simulates LLM extraction)
        const domText = await page.evaluate(() => {
            return document.body.textContent || '';
        });
        
        // Extract visible text only
        const bodyElement = await page.$('body');
        const visibleText = await extractVisibleText(bodyElement);
        
        // Find all tokens in the file
        const tokens = [];
        const tokenRegex = /PHANTOM_TEST_TOKEN_(\w+)/g;
        let match;
        while ((match = tokenRegex.exec(domText)) !== null) {
            tokens.push(match[0]);
        }
        
        // Check each token
        const results = [];
        for (const token of tokens) {
            const attackId = token.replace('PHANTOM_TEST_TOKEN_', '');
            const domHasToken = domText.includes(token);
            const visibleHasToken = visibleText.includes(token);
            
            results.push({
                attack_id: attackId,
                token: token,
                dom_has_token: domHasToken,
                visible_has_token: visibleHasToken,
                passed: domHasToken && !visibleHasToken
            });
            
            logger.info(`  Token: ${token}`);
            logger.info(`    DOM has token: ${domHasToken}`);
            logger.info(`    Visible has token: ${visibleHasToken}`);
            logger.info(`    Audit passed: ${domHasToken && !visibleHasToken}`);
        }
        
        const duration = Date.now() - startTime;
        logger.info(`Audit completed in ${duration}ms`);
        
        return {
            file_path: filePath,
            dom_text_length: domText.length,
            visible_text_length: visibleText.length,
            tokens_found: tokens.length,
            results: results,
            duration_ms: duration
        };
    } catch (error) {
        logger.error(`Error auditing file ${filePath}: ${error.message}`);
        return {
            file_path: filePath,
            error: error.message
        };
    }
}

/**
 * Main audit function.
 */
async function auditVisibility(baselineFile, attackedDir, reportsDir) {
    const logger = setupLogging();
    
    logger.info('='.repeat(80));
    logger.info('Starting visibility audit');
    logger.info('='.repeat(80));
    
    // Validate inputs
    if (!fs.existsSync(baselineFile)) {
        logger.error(`Baseline file not found: ${baselineFile}`);
        process.exit(1);
    }
    
    if (!fs.existsSync(attackedDir)) {
        logger.error(`Attacked directory not found: ${attackedDir}`);
        process.exit(1);
    }
    
    // Create reports directory
    if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
    }
    
    logger.info(`Baseline file: ${baselineFile}`);
    logger.info(`Attacked directory: ${attackedDir}`);
    logger.info(`Reports directory: ${reportsDir}`);
    
    // Launch browser
    logger.info('Launching browser...');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const auditResults = [];
    
    try {
        // Audit baseline
        logger.info('-'.repeat(80));
        logger.info('Auditing baseline file');
        const baselineResult = await auditFile(page, path.resolve(baselineFile), logger);
        auditResults.push(baselineResult);
        
        // Audit attacked files
        logger.info('-'.repeat(80));
        logger.info('Auditing attacked files');
        const files = fs.readdirSync(attackedDir)
            .filter(f => f.endsWith('.html'))
            .map(f => path.join(attackedDir, f));
        
        logger.info(`Found ${files.length} attacked file(s)`);
        
        for (const file of files) {
            const result = await auditFile(page, path.resolve(file), logger);
            auditResults.push(result);
        }
        
    } finally {
        await browser.close();
    }
    
    // Generate summary statistics
    logger.info('='.repeat(80));
    logger.info('Generating summary statistics');
    
    const summary = {
        total_files: auditResults.length,
        baseline_files: 1,
        attacked_files: auditResults.length - 1,
        total_tokens_found: 0,
        passed_audits: 0,
        failed_audits: 0
    };
    
    const detailedResults = [];
    
    for (const result of auditResults) {
        if (result.error) {
            logger.warn(`File ${result.file_path} had errors`);
            continue;
        }
        
        for (const tokenResult of result.results || []) {
            summary.total_tokens_found++;
            if (tokenResult.passed) {
                summary.passed_audits++;
            } else {
                summary.failed_audits++;
            }
            
            detailedResults.push({
                file: path.basename(result.file_path),
                attack_id: tokenResult.attack_id,
                token: tokenResult.token,
                dom_has_token: tokenResult.dom_has_token,
                visible_has_token: tokenResult.visible_has_token,
                audit_passed: tokenResult.passed
            });
        }
    }
    
    logger.info(`Total files audited: ${summary.total_files}`);
    logger.info(`Total tokens found: ${summary.total_tokens_found}`);
    logger.info(`Passed audits: ${summary.passed_audits}`);
    logger.info(`Failed audits: ${summary.failed_audits}`);
    
    // Write JSON report
    const jsonReport = {
        summary: summary,
        results: auditResults,
        detailed_results: detailedResults,
        generated_at: new Date().toISOString()
    };
    
    const jsonPath = path.join(reportsDir, 'audit_results.json');
    logger.info(`Writing JSON report to: ${jsonPath}`);
    fs.writeFileSync(jsonPath, JSON.stringify(jsonReport, null, 2));
    
    // Write CSV report
    const csvPath = path.join(reportsDir, 'audit_results.csv');
    logger.info(`Writing CSV report to: ${csvPath}`);
    
    const csvHeaders = ['file', 'attack_id', 'token', 'dom_has_token', 'visible_has_token', 'audit_passed'];
    const csvRows = detailedResults.map(r => [
        r.file,
        r.attack_id,
        r.token,
        r.dom_has_token,
        r.visible_has_token,
        r.audit_passed
    ]);
    
    const csvContent = [
        csvHeaders.join(','),
        ...csvRows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    fs.writeFileSync(csvPath, csvContent);
    
    logger.info('='.repeat(80));
    logger.info('Audit complete');
    logger.info(`JSON report: ${jsonPath}`);
    logger.info(`CSV report: ${csvPath}`);
    logger.info('='.repeat(80));
    
    logger.close();
}

// Main execution
if (require.main === module) {
    if (process.argv.length !== 5) {
        console.error('Usage: node 04_audit_visibility.js <baseline_html> <attacked_dir> <reports_dir>');
        process.exit(1);
    }
    
    const baselineFile = process.argv[2];
    const attackedDir = process.argv[3];
    const reportsDir = process.argv[4];
    
    auditVisibility(baselineFile, attackedDir, reportsDir)
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}

module.exports = { auditVisibility, auditFile, extractVisibleText };

