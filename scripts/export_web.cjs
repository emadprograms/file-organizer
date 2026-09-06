#!/usr/bin/env node
/**
 * Node.js Static Web Exporter for File Organizer
 * Generates tree.json, search_index.json, web.config, and copies index.html
 * Runs on Node.js without requiring Python runtime.
 */
const fs = require('fs');
const path = require('path');

const WEB_CONFIG_TEMPLATE = `<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <staticContent>
            <!-- Remove existing mappings to prevent duplicate MIME type errors -->
            <remove fileExtension=".json" />
            <remove fileExtension=".pdf" />
            <mimeMap fileExtension=".json" mimeType="application/json" />
            <mimeMap fileExtension=".pdf" mimeType="application/pdf" />
        </staticContent>
        <defaultDocument enabled="true">
            <files>
                <clear />
                <add value="index.html" />
            </files>
        </defaultDocument>
        <httpProtocol>
            <customHeaders>
                <add name="Access-Control-Allow-Origin" value="*" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
`;

function getDocumentGroups(stateData) {
    const routed = stateData.routed_documents || [];
    if (Array.isArray(routed) && routed.length > 0 && routed[0].vault_id) return routed;
    const grouped = stateData.grouped_documents || [];
    if (Array.isArray(grouped) && grouped.length > 0 && grouped[0].vault_id) return grouped;
    if (Array.isArray(routed) && routed.length > 0) return routed;
    if (Array.isArray(grouped) && grouped.length > 0) return grouped;
    return [];
}

function buildTreeData(areasRoot) {
    const tree = [];
    if (!fs.existsSync(areasRoot)) return tree;

    const areaEntries = fs.readdirSync(areasRoot, { withFileTypes: true });
    for (const areaEntry of areaEntries) {
        if (!areaEntry.isDirectory()) continue;
        if (areaEntry.name.startsWith('.') || areaEntry.name.startsWith('_')) continue;
        if (['node_modules', 'src', 'docs', 'tests', 'scripts', '.git'].includes(areaEntry.name)) continue;

        const areaPath = path.join(areasRoot, areaEntry.name);
        const houseEntries = fs.readdirSync(areaPath, { withFileTypes: true });
        const houseChildren = [];

        for (const houseEntry of houseEntries) {
            if (!houseEntry.isDirectory()) continue;
            if (houseEntry.name.startsWith('.') || houseEntry.name.startsWith('_')) continue;

            const housePath = path.join(areaPath, houseEntry.name);
            const sfPath = path.join(housePath, '.source_files');
            const houseId = houseEntry.name.includes(' - ') ? houseEntry.name.split(' - ')[0] : houseEntry.name;
            const stateFile = path.join(sfPath, `${houseId}_state.json`);

            const tenantChildren = [];
            const tenantsWithDates = {};
            const tenantIsPresent = {};
            const categoryCounts = {};
            let totalDocs = 0;

            if (fs.existsSync(stateFile)) {
                try {
                    const raw = fs.readFileSync(stateFile, 'utf8');
                    const stateData = JSON.parse(raw);

                    if (stateData.manifest && Array.isArray(stateData.manifest.per_page)) {
                        for (const page of stateData.manifest.per_page) {
                            const tenant = page.tenant;
                            const tf = page.target_folder || '';
                            if (tenant && (tf.includes('الآن') || tf.toLowerCase().includes('present'))) {
                                tenantIsPresent[tenant] = true;
                            }
                        }
                    }

                    const groups = getDocumentGroups(stateData);
                    totalDocs = groups.length;
                    for (const doc of groups) {
                        const tenant = doc.primary_tenant;
                        const catRaw = doc.folder_path || doc.category;
                        if (catRaw) {
                            const cleanCat = catRaw.replace(/^\d+\s*-\s*/, '');
                            categoryCounts[cleanCat] = (categoryCounts[cleanCat] || 0) + 1;
                        }

                        if (tenant) {
                            if (!tenantsWithDates[tenant]) tenantsWithDates[tenant] = [];
                            const dates = doc.dates || [];
                            for (const d of dates) {
                                if (d && d !== 'NONE') {
                                    const m = d.match(/(\d{4})/);
                                    if (m) tenantsWithDates[tenant].push(parseInt(m[1], 10));
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.error(`Error parsing ${stateFile}:`, e.message);
                }
            }

            const currentYear = new Date().getFullYear();
            for (const [t, years] of Object.entries(tenantsWithDates)) {
                let subtitle = null;
                let durationCategory = null;
                if (years.length > 0) {
                    const minVal = Math.min(...years);
                    const maxVal = Math.max(...years);

                    if (tenantIsPresent[t]) {
                        const duration = currentYear - minVal;
                        if (duration < 5) durationCategory = 'short';
                        else if (duration < 10) durationCategory = 'medium';
                        else durationCategory = 'long';
                        subtitle = `${minVal} - Present`;
                    } else if (minVal === maxVal) {
                        subtitle = `${minVal}`;
                    } else {
                        subtitle = `${minVal} - ${maxVal}`;
                    }
                }

                tenantChildren.push({
                    id: `${houseEntry.name}_${t}`,
                    name: t,
                    subtitle: subtitle,
                    duration_category: durationCategory,
                    type: 'tenant',
                    children: []
                });
            }

            // Determine active tenant and house-level metrics
            let activeTenant = null;
            for (const t of Object.keys(tenantsWithDates)) {
                if (tenantIsPresent[t]) {
                    activeTenant = t;
                    break;
                }
            }
            if (!activeTenant && houseEntry.name.includes(' - ')) {
                const cand = houseEntry.name.split(' - ')[1].trim();
                if (tenantsWithDates[cand]) activeTenant = cand;
            }
            if (!activeTenant && Object.keys(tenantsWithDates).length === 1) {
                activeTenant = Object.keys(tenantsWithDates)[0];
            }

            let houseDurationCat = null;
            let houseSub = null;
            if (activeTenant && tenantsWithDates[activeTenant] && tenantsWithDates[activeTenant].length > 0) {
                const years = tenantsWithDates[activeTenant];
                const minVal = Math.min(...years);
                const maxVal = Math.max(...years);
                const isPres = !!tenantIsPresent[activeTenant];
                if (isPres || activeTenant === (houseEntry.name.includes(' - ') ? houseEntry.name.split(' - ')[1].trim() : '')) {
                    const duration = currentYear - minVal;
                    if (duration < 5) houseDurationCat = 'short';
                    else if (duration < 10) houseDurationCat = 'medium';
                    else houseDurationCat = 'long';
                    houseSub = `Since ${minVal} (${duration}y)`;
                } else if (minVal === maxVal) {
                    houseSub = `${minVal}`;
                } else {
                    houseSub = `${minVal} - ${maxVal}`;
                }
            }

            houseChildren.push({
                id: houseEntry.name,
                name: houseEntry.name,
                type: 'house',
                current_tenant: activeTenant,
                duration_category: houseDurationCat,
                subtitle: houseSub,
                total_documents: totalDocs,
                category_counts: categoryCounts,
                children: tenantChildren
            });
        }

        tree.push({
            id: areaEntry.name,
            name: areaEntry.name,
            type: 'area',
            children: houseChildren
        });
    }

    return tree;
}

function buildSearchIndex(areasRoot) {
    const searchData = {
        houses: [],
        tenants: [],
        documents: []
    };
    if (!fs.existsSync(areasRoot)) return searchData;

    const areaEntries = fs.readdirSync(areasRoot, { withFileTypes: true });
    for (const areaEntry of areaEntries) {
        if (!areaEntry.isDirectory()) continue;
        if (areaEntry.name.startsWith('.') || areaEntry.name.startsWith('_')) continue;
        if (['node_modules', 'src', 'docs', 'tests', 'scripts', '.git'].includes(areaEntry.name)) continue;

        const areaPath = path.join(areasRoot, areaEntry.name);
        const houseEntries = fs.readdirSync(areaPath, { withFileTypes: true });

        for (const houseEntry of houseEntries) {
            if (!houseEntry.isDirectory()) continue;
            if (houseEntry.name.startsWith('.') || houseEntry.name.startsWith('_')) continue;

            searchData.houses.push({
                area_name: areaEntry.name,
                house_dir_name: houseEntry.name
            });

            const housePath = path.join(areaPath, houseEntry.name);
            const sfPath = path.join(housePath, '.source_files');
            const houseId = houseEntry.name.includes(' - ') ? houseEntry.name.split(' - ')[0] : houseEntry.name;
            const stateFile = path.join(sfPath, `${houseId}_state.json`);
            const reportFile = path.join(sfPath, `${houseId}_report.json`);

            const seenTenants = new Set();
            let stateGroups = [];

            if (fs.existsSync(stateFile)) {
                try {
                    const raw = fs.readFileSync(stateFile, 'utf8');
                    const stateData = JSON.parse(raw);
                    stateGroups = getDocumentGroups(stateData);

                    for (const doc of stateGroups) {
                        const tenant = doc.primary_tenant;
                        if (tenant && !seenTenants.has(tenant)) {
                            seenTenants.add(tenant);
                            searchData.tenants.push({
                                area_name: areaEntry.name,
                                house_dir_name: houseEntry.name,
                                tenant_name: tenant
                            });
                        }
                    }
                } catch (e) {}
            }

            if (fs.existsSync(reportFile)) {
                try {
                    const raw = fs.readFileSync(reportFile, 'utf8');
                    const reportData = JSON.parse(raw);
                    const reportDocs = reportData.documents || [];
                    for (const doc of reportDocs) {
                        const vaultId = doc.vault_id || '';
                        const docTitle = doc.brief_arabic_title || 'Untitled';
                        const content = (doc.content || '').toLowerCase();
                        searchData.documents.push({
                            area_name: areaEntry.name,
                            house_dir_name: houseEntry.name,
                            vault_id: vaultId,
                            doc_title: docTitle,
                            title_field: docTitle.toLowerCase(),
                            content: content
                        });
                    }
                } catch (e) {}
            } else {
                for (const doc of stateGroups) {
                    const vaultId = doc.vault_id || '';
                    const docTitle = doc.brief_arabic_title || 'Untitled';
                    searchData.documents.push({
                        area_name: areaEntry.name,
                        house_dir_name: houseEntry.name,
                        vault_id: vaultId,
                        doc_title: docTitle,
                        title_field: docTitle.toLowerCase(),
                        content: ''
                    });
                }
            }
        }
    }

    return searchData;
}

function exportStaticWeb(areasRoot, outputDir) {
    if (!outputDir) outputDir = areasRoot;
    fs.mkdirSync(outputDir, { recursive: true });

    console.log(`[export-web] Building tree and search index from: ${areasRoot}`);
    const treeData = buildTreeData(areasRoot);
    const searchData = buildSearchIndex(areasRoot);

    const treePath = path.join(outputDir, 'tree.json');
    const searchPath = path.join(outputDir, 'search_index.json');
    const webConfigPath = path.join(outputDir, 'web.config');
    const indexPath = path.join(outputDir, 'index.html');

    fs.writeFileSync(treePath, JSON.stringify(treeData, null, 2), 'utf8');
    console.log(`[export-web] Created ${treePath} (${treeData.length} areas)`);

    fs.writeFileSync(searchPath, JSON.stringify(searchData, null, 2), 'utf8');
    console.log(`[export-web] Created ${searchPath} (${searchData.houses.length} houses, ${searchData.tenants.length} tenants, ${searchData.documents.length} docs)`);

    fs.writeFileSync(webConfigPath, WEB_CONFIG_TEMPLATE, 'utf8');
    console.log(`[export-web] Created ${webConfigPath}`);

    const sourceHtml = path.resolve(__dirname, '../src/api/static/index.html');
    if (fs.existsSync(sourceHtml)) {
        fs.copyFileSync(sourceHtml, indexPath);
        console.log(`[export-web] Copied index.html to ${indexPath}`);
    } else {
        console.warn(`[export-web] Warning: Source ${sourceHtml} not found`);
    }

    console.log(`\n[export-web] SUCCESS! Static web dashboard ready at: ${outputDir}`);
}

// CLI entry point
const args = process.argv.slice(2);
let areasDir = args[0] || path.resolve(__dirname, '../tests/fixtures/e2e/golden_state/areas');
let outDir = args[1] || areasDir;

if (args.includes('--help') || args.includes('-h')) {
    console.log(`Usage: node scripts/export_web.cjs [areas_dir] [output_dir]`);
    process.exit(0);
}

exportStaticWeb(areasDir, outDir);
