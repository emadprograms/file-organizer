// ── Document Viewer Component ─────────────────────────────────────────────
(function() {
    let currentPinnedDoc = null;
    let currentPdfDoc = null;
    let currentPdfUrl = null;
    let currentScale = 1.0;
    let currentScaleMode = 'fit'; // 'fit' or 'manual'
    let currentLoadingTask = null;

    // ── Offline English Translation Knowledge Base & Engine ──────────────
    const CATEGORY_TRANSLATIONS = {
        '01 - بيانات أساسية': { en: 'Basic Application Details', icon: '📝' },
        '02 - بيانات شخصية': { en: 'Personal Identity & CPR Documents', icon: '🪪' },
        '03 - أمر تخصيص': { en: 'Housing Allocation Order', icon: '🏛️' },
        '04 - محضر تسليم مفتاح': { en: 'Key Handover Minutes', icon: '🔑' },
        '05 - عقود': { en: 'Lease & Tenancy Contract', icon: '📜' },
        '06 - كهرباء وماء': { en: 'Electricity & Water (EWA) Utility Bill', icon: '⚡' },
        '07 - استقطاع إيجار': { en: 'Rent Deduction Notice', icon: '💳' },
        '08 - وقف استقطاع بدل': { en: 'Stop Housing Allowance Deduction Request', icon: '🛑' },
        '09 - إشعارات': { en: 'Official Notices & Eviction Warnings', icon: '⚠️' },
        '10 - صيانة': { en: 'Maintenance & Repair Request', icon: '🔧' },
        '11 - صور ومعاينات': { en: 'Site Inspection Report & Photos', icon: '📷' },
        '12 - تعديلات': { en: 'Housing Renovation & Modifications', icon: '🏗️' },
        '13 - رسائل متنوعة': { en: 'Official Correspondence & Letters', icon: '✉️' }
    };

    // ── Document Phrases & Entities Dictionary (Longest first, boundary-aware) ──
    const ARABIC_PHRASES = [
        // ── Government & Authorities ──
        { ar: 'مكتب وزير الداخلية', en: 'Office of the Minister of Interior' },
        { ar: 'مكتب وكيل وزارة الداخلية', en: 'Office of the Undersecretary of the Ministry of Interior' },
        { ar: 'لجنة دراسة الخدمات الإسكانية للسادة الضباط والرتب الأخرى', en: 'Housing Services Committee for Officers and Other Ranks' },
        { ar: 'لجنة دراسة الخدمات الإسكانية للضباط', en: 'Housing Services Committee for Officers' },
        { ar: 'لجنة دراسة الخدمات الإسكانية', en: 'Housing Services Committee' },
        { ar: 'الوكيل المساعد للشئون الإدارية', en: 'Assistant Undersecretary for Administrative Affairs' },
        { ar: 'الوكيل المساعد للشؤون الإدارية', en: 'Assistant Undersecretary for Administrative Affairs' },
        { ar: 'الوكيل المساعد للشؤون المالية', en: 'Assistant Undersecretary for Financial Affairs' },
        { ar: 'وكيل وزارة الداخلية', en: 'Undersecretary of the Ministry of Interior' },
        { ar: 'وزارة الإسكان والتخطيط العمراني', en: 'Ministry of Housing and Urban Planning' },
        { ar: 'وزارة شؤون البلديات والزراعة', en: 'Ministry of Municipalities Affairs and Agriculture' },
        { ar: 'وزارة العدل والشئون الإسلامية والأوقاف', en: 'Ministry of Justice & Islamic Affairs' },
        { ar: 'وزارة العدل والشؤون الإسلامية والأوقاف', en: 'Ministry of Justice & Islamic Affairs' },
        { ar: 'وزارة المالية والاقتصاد الوطني', en: 'Ministry of Finance & National Economy' },
        { ar: 'وزارة الأشغال وشئون البلديات والتخطيط العمراني', en: 'Ministry of Works & Municipalities Affairs' },
        { ar: 'الإدارة العامة للمرور', en: 'General Directorate of Traffic' },
        { ar: 'الإدارة العامة للدفاع المدني', en: 'General Directorate of Civil Defence' },
        { ar: 'الإدارة العامة للمباحث والأدلة الجنائية', en: 'General Directorate of Criminal Investigation & Forensic Science' },
        { ar: 'إدارة الإمداد والتموين', en: 'Directorate of Supply and Catering' },
        { ar: 'إدارة الإمداد والتنوين', en: 'Directorate of Supply and Catering' },
        { ar: 'إدارة المحاكم العسكرية', en: 'Directorate of Military Courts' },
        { ar: 'إدارة الخدمات الإسكانية', en: 'Housing Services Directorate' },
        { ar: 'إدارة صيانة الوحدات السكنية', en: 'Housing Units Maintenance Directorate' },
        { ar: 'إدارة الممتلكات والإنشاءات', en: 'Properties and Construction Directorate' },
        { ar: 'إدارة الشؤون القانونية', en: 'Legal Affairs Directorate' },
        { ar: 'إدارة الشئون القانونية', en: 'Legal Affairs Directorate' },
        { ar: 'إدارة الموارد البشرية', en: 'Human Resources Directorate' },
        { ar: 'إدارة الموارد المالية', en: 'Financial Resources Directorate' },
        { ar: 'إدارة التوثيق', en: 'Notarization Directorate' },
        { ar: 'هيئة الكهرباء والماء', en: 'Electricity & Water Authority (EWA)' },
        { ar: 'فرع إسكان الشرطة', en: 'Police Housing Branch' },
        { ar: 'فرع القضايا العامة', en: 'General Cases Branch' },
        { ar: 'شعبة الإسكان', en: 'Housing Division' },
        { ar: 'قسم التخصيص', en: 'Allocation Section' },
        { ar: 'قسم الصيانة', en: 'Maintenance Section' },
        { ar: 'قسم التحصيل', en: 'Collection Section' },
        { ar: 'قسم الحسابات', en: 'Accounts Section' },
        { ar: 'رئاسة الأمن العام', en: 'Public Security Headquarters' },
        { ar: 'قوة دفاع البحرين', en: 'Bahrain Defence Force' },
        { ar: 'الحرس الوطني', en: 'National Guard' },
        { ar: 'جهاز الأمن الوطني', en: 'National Security Agency' },
        { ar: 'الديوان الملكي', en: 'Royal Court' },
        { ar: 'ديوان ولي العهد', en: 'Crown Prince Court' },
        { ar: 'ديوان الرقابة المالية والإدارية', en: 'National Audit Office' },
        { ar: 'ديوان الخدمة المدنية', en: 'Civil Service Bureau' },
        { ar: 'شئون الجمارك', en: 'Customs Affairs' },
        { ar: 'شؤون الجمارك', en: 'Customs Affairs' },
        { ar: 'وزارة الداخلية', en: 'Ministry of Interior' },
        { ar: 'وزارة الإسكان', en: 'Ministry of Housing' },
        { ar: 'وزارة العدل', en: 'Ministry of Justice' },
        { ar: 'وزارة الأشغال', en: 'Ministry of Works' },
        { ar: 'القيادة العامة', en: 'General Command' },
        { ar: 'مملكة البحرين', en: 'Kingdom of Bahrain' },
        { ar: 'الوكيل المساعد', en: 'Assistant Undersecretary' },
        { ar: 'وكيل الوزارة', en: 'Undersecretary of the Ministry' },
        { ar: 'وزير الداخلية', en: 'Minister of Interior' },

        // ── Document Names & Headings ──
        { ar: 'إشعار بإخلاء الوحدة السكنية', en: 'Housing Unit Eviction Notice' },
        { ar: 'إشعار إخلاء وحدة سكنية', en: 'Housing Unit Eviction Notice' },
        { ar: 'إشعار إخلاء مسكن', en: 'House Eviction Notice' },
        { ar: 'إشعارات الإخلاء', en: 'Eviction Notices' },
        { ar: 'إشعارات إخلاء', en: 'Eviction Notices' },
        { ar: 'إشعار إخلاء', en: 'Eviction Notice' },
        { ar: 'إنذار بإخلاء', en: 'Eviction Warning Notice' },
        { ar: 'إنذار نهائي بالإخلاء', en: 'Final Eviction Warning' },
        { ar: 'إنذار نهائي', en: 'Final Warning' },
        { ar: 'إشعار نهائي', en: 'Final Notice' },
        { ar: 'إشعار بالسداد', en: 'Payment Notice' },
        { ar: 'إشعار بالمراجعة', en: 'Notice to Report / Review' },
        { ar: 'إشعار بقطع الخدمة', en: 'Service Disconnection Notice' },
        { ar: 'قطع التيار الكهربائي', en: 'Electricity Disconnection' },
        { ar: 'إعادة التيار الكهربائي', en: 'Electricity Reconnection' },
        { ar: 'براءة ذمة مالية', en: 'Financial Clearance Certificate' },
        { ar: 'شهادة براءة ذمة', en: 'Clearance Certificate' },
        { ar: 'براءة ذمة', en: 'Clearance Certificate' },
        { ar: 'إقرار إخلاء وحدة سكنية', en: 'Housing Unit Evacuation Undertaking' },
        { ar: 'إقرار إخلاء مسكن', en: 'Housing Evacuation Undertaking' },
        { ar: 'إقرار إخلاء', en: 'Evacuation Undertaking' },
        { ar: 'إقرار وتعهد', en: 'Declaration and Undertaking' },
        { ar: 'إقرار استلام', en: 'Receipt Acknowledgment' },
        { ar: 'إقرار خطي', en: 'Written Declaration' },
        { ar: 'بإخلاء الوحدة السكنية رقم', en: 'to vacate Housing Unit No.' },
        { ar: 'بإخلاء الوحدة السكنية', en: 'to vacate Housing Unit' },
        { ar: 'بإخلاء وحدة سكنية', en: 'to vacate housing unit' },
        { ar: 'بإخلاء المسكن', en: 'to vacate residence' },
        { ar: 'بإخلاء مسكن', en: 'to vacate residence' },
        { ar: 'بإخلاء', en: 'to vacate' },
        { ar: 'بمنطقة سافرة', en: 'in Safra Area' },
        { ar: 'بمنطقة سافر', en: 'in Safra Area' },
        { ar: 'بمنطقة مسافر', en: 'in Saafer Area' },
        { ar: 'بمنطقة عوالي', en: 'in Awali Area' },
        { ar: 'بمنطقة الرفاع', en: 'in Riffa Area' },
        { ar: 'بمنطقة', en: 'in Area' },
        { ar: 'بالمسكن', en: 'in residence' },
        { ar: 'بالوحدة السكنية', en: 'in housing unit' },
        { ar: 'بالوحدة', en: 'in unit' },
        { ar: 'بالعقد', en: 'in contract' },
        { ar: 'بحضور', en: 'in the presence of' },
        { ar: 'آل خليفة', en: 'Al Khalifa' },
        { ar: 'آل دوسري', en: 'Al Doseri' },
        { ar: 'آل نعيمي', en: 'Al Nuaimi' },
        { ar: 'آل ثاني', en: 'Al Thani' },
        { ar: 'آل سعود', en: 'Al Saud' },
        { ar: 'آل صباح', en: 'Al Sabah' },
        { ar: 'بن راشد', en: 'Bin Rashid' },
        { ar: 'بن علي', en: 'Bin Ali' },
        { ar: 'بن أحمد', en: 'Bin Ahmed' },
        { ar: 'بن محمد', en: 'Bin Mohamed' },
        { ar: 'طلب الانتفاع بالوحدة السكنية', en: 'Application to Benefit from Housing Unit' },
        { ar: 'طلب انتفاع بالمسكن', en: 'Housing Occupancy Application' },
        { ar: 'طلب انتفاع', en: 'Housing Beneficiary Application' },
        { ar: 'المخالفين لنظام الانتفاع', en: 'Violators of Housing Occupancy Regulations' },
        { ar: 'مخالفي نظام الانتفاع', en: 'Housing Occupancy Regulation Violators' },
        { ar: 'نظام الانتفاع بالوحدات السكنية', en: 'Housing Occupancy Regulations' },
        { ar: 'نظام الانتفاع', en: 'Occupancy Regulations' },
        { ar: 'محضر تسليم مفتاح', en: 'Key Handover Minutes' },
        { ar: 'محضر تسليم المفاتيح', en: 'Keys Handover Minutes' },
        { ar: 'محضر استلام مفتاح', en: 'Key Handover Confirmation' },
        { ar: 'محضر استلام المفاتيح', en: 'Key Handover Confirmation' },
        { ar: 'محضر تسليم مسكن', en: 'House Handover Record' },
        { ar: 'محضر تسليم', en: 'Handover Minutes' },
        { ar: 'محضر استلام مسكن', en: 'House Handover Confirmation' },
        { ar: 'محضر استلام', en: 'Handover Confirmation Record' },
        { ar: 'محضر اجتماع', en: 'Minutes of Meeting' },
        { ar: 'محضر معاينة', en: 'Inspection Minutes' },
        { ar: 'تقرير معاينة', en: 'Site Inspection Report' },
        { ar: 'أمر تخصيص مسكن', en: 'Housing Allocation Order' },
        { ar: 'أمر تخصيص وحدة سكنية', en: 'Housing Unit Allocation Order' },
        { ar: 'أمر تخصيص', en: 'Housing Allocation Order' },
        { ar: 'طلب صيانة وإصلاح', en: 'Maintenance & Repair Request' },
        { ar: 'طلب صيانة مسكن', en: 'Housing Maintenance Request' },
        { ar: 'طلب صيانة', en: 'Maintenance Request' },
        { ar: 'عقد إيجار موثق', en: 'Notarized Tenancy Contract' },
        { ar: 'عقد إيجار سكني', en: 'Residential Tenancy Agreement' },
        { ar: 'عقد إيجار', en: 'Lease & Tenancy Contract' },
        { ar: 'عقد ايجار', en: 'Lease & Tenancy Contract' },
        { ar: 'اتفاقية إيجار', en: 'Tenancy Agreement' },
        { ar: 'اتفاقية ايجار', en: 'Tenancy Agreement' },
        { ar: 'ملحق عقد', en: 'Contract Addendum' },
        { ar: 'فاتورة كهرباء وماء', en: 'Electricity & Water Utility Bill' },
        { ar: 'فاتورة كهرباء', en: 'Electricity Bill' },
        { ar: 'فاتورة ماء', en: 'Water Bill' },
        { ar: 'فاتورة استهلاك', en: 'Utility Consumption Bill' },
        { ar: 'استقطاع إيجار شهري', en: 'Monthly Rent Deduction' },
        { ar: 'استقطاع إيجار', en: 'Rent Deduction Notice' },
        { ar: 'وقف استقطاع بدل سكن', en: 'Stop Housing Allowance Deduction Request' },
        { ar: 'طلب بدل سكن', en: 'Housing Allowance Request' },
        { ar: 'استحقاق بدل سكن', en: 'Housing Allowance Entitlement' },
        { ar: 'وقف بدل سكن', en: 'Stop Housing Allowance Request' },
        { ar: 'بدل سكن', en: 'Housing Allowance' },
        { ar: 'شهادة راتب', en: 'Salary Certificate' },
        { ar: 'كشف حساب بنكي', en: 'Bank Statement' },
        { ar: 'كشف حساب', en: 'Account Statement' },
        { ar: 'بطاقة الهوية', en: 'National Identity Card (CPR)' },
        { ar: 'بطاقة شخصية', en: 'CPR Identity Card' },
        { ar: 'الرقم الشخصي', en: 'CPR / ID Number' },
        { ar: 'رقم الهوية', en: 'CPR / ID Number' },
        { ar: 'جواز السفر', en: 'Passport' },

        // ── Legal & Contract Terms ──
        { ar: 'اتفق الطرفان على ما يلي', en: 'Both parties agreed to the following' },
        { ar: 'تم الاتفاق بين الطرفين', en: 'Agreement was reached between both parties' },
        { ar: 'أقر أنا الموقع أدناه', en: 'I, the undersigned, hereby declare' },
        { ar: 'أقر الموقع أدناه', en: 'The undersigned hereby declares' },
        { ar: 'الموقع أدناه', en: 'The Undersigned' },
        { ar: 'والطرف الأول (المؤجر)', en: 'and the First Party (Lessor)' },
        { ar: 'والطرف الثاني (المستأجر)', en: 'and the Second Party (Tenant)' },
        { ar: 'والطرف الأول', en: 'and the First Party' },
        { ar: 'والطرف الثاني', en: 'and the Second Party' },
        { ar: 'والمستأجر', en: 'and the Tenant' },
        { ar: 'والمؤجر', en: 'and the Lessor' },
        { ar: 'الطرف الأول (المؤجر)', en: 'First Party (Lessor)' },
        { ar: 'الطرف الثاني (المستأجر)', en: 'Second Party (Tenant)' },
        { ar: 'الطرف الأول', en: 'First Party' },
        { ar: 'الطرف الثاني', en: 'Second Party' },
        { ar: 'الطرفان', en: 'Both Parties' },
        { ar: 'المستأجر', en: 'Tenant' },
        { ar: 'المؤجر', en: 'Lessor / Landlord' },
        { ar: 'قيمة الإيجار الشهري', en: 'Monthly Rental Value' },
        { ar: 'قيمة الإيجار', en: 'Rental Value' },
        { ar: 'مبلغ الإيجار', en: 'Rent Amount' },
        { ar: 'الإيجار الشهري', en: 'Monthly Rent' },
        { ar: 'الأجرة الشهرية', en: 'Monthly Rent Fee' },
        { ar: 'قيمة الأجرة', en: 'Rent Fee Value' },
        { ar: 'مدة العقد', en: 'Contract Duration' },
        { ar: 'تاريخ بدء العقد', en: 'Contract Start Date' },
        { ar: 'تاريخ انتهاء العقد', en: 'Contract End Date' },
        { ar: 'تاريخ التوقيع', en: 'Date of Signing' },
        { ar: 'تاريخ التحرير', en: 'Date of Execution' },
        { ar: 'يلتزم المستأجر', en: 'The Tenant undertakes' },
        { ar: 'يلتزم المؤجر', en: 'The Lessor undertakes' },
        { ar: 'يتعهد المستأجر', en: 'The Tenant pledges' },
        { ar: 'شروط العقد', en: 'Contract Terms & Conditions' },
        { ar: 'الشروط والأحكام', en: 'Terms and Conditions' },
        { ar: 'بنود العقد', en: 'Contract Clauses' },
        { ar: 'البند الأول', en: 'Clause 1' },
        { ar: 'البند الثاني', en: 'Clause 2' },
        { ar: 'البند الثالث', en: 'Clause 3' },
        { ar: 'البند الرابع', en: 'Clause 4' },
        { ar: 'البند الخامس', en: 'Clause 5' },
        { ar: 'البند السادس', en: 'Clause 6' },
        { ar: 'البند السابع', en: 'Clause 7' },
        { ar: 'البند الثامن', en: 'Clause 8' },
        { ar: 'البند التاسع', en: 'Clause 9' },
        { ar: 'البند العاشر', en: 'Clause 10' },
        { ar: 'تأمين الإيجار', en: 'Rental Security Deposit' },
        { ar: 'مبلغ التأمين', en: 'Deposit Amount' },
        { ar: 'العين المؤجرة', en: 'Leased Property' },
        { ar: 'الوحدة المؤجرة', en: 'Leased Unit' },
        { ar: 'العقار المؤجر', en: 'Leased Premises' },
        { ar: 'إخلاء المأجور', en: 'Vacate Leased Premises' },
        { ar: 'استهلاك الكهرباء والماء', en: 'Electricity & Water Consumption' },
        { ar: 'حساب المشترك', en: 'Subscriber Account' },
        { ar: 'رقم الحساب', en: 'Account No.' },
        { ar: 'رقم العداد', en: 'Meter No.' },
        { ar: 'قراءة العداد', en: 'Meter Reading' },
        { ar: 'المبلغ المستحق', en: 'Amount Due' },
        { ar: 'المبلغ الإجمالي', en: 'Total Amount' },
        { ar: 'المجموع الكلي', en: 'Grand Total' },
        { ar: 'الرصيد السابق', en: 'Previous Balance' },
        { ar: 'الرصيد الحالي', en: 'Current Balance' },
        { ar: 'تاريخ الاستحقاق', en: 'Due Date' },
        { ar: 'تم السداد', en: 'Paid' },
        { ar: 'تم دفع', en: 'Paid' },
        { ar: 'غير مدفوع', en: 'Unpaid' },
        { ar: 'إنهاء العقد', en: 'Contract Termination' },
        { ar: 'فسخ العقد', en: 'Contract Rescission' },
        { ar: 'تجديد العقد', en: 'Contract Renewal' },
        { ar: 'توقيع الطرف الأول', en: 'First Party Signature' },
        { ar: 'توقيع الطرف الثاني', en: 'Second Party Signature' },
        { ar: 'توقيع المستأجر', en: 'Tenant Signature' },
        { ar: 'توقيع المؤجر', en: 'Lessor Signature' },
        { ar: 'ختم الإدارة', en: 'Directorate Official Stamp' },
        { ar: 'ختم رسمي', en: 'Official Stamp' },
        { ar: 'كاتب العدل', en: 'Notary Public' },
        { ar: 'مكتب التوثيق', en: 'Notarization Office' },
        { ar: 'حظر التأجير من الباطن', en: 'Subletting Prohibition' },
        { ar: 'التأجير من الباطن', en: 'Subletting' },
        { ar: 'التنازل للغير', en: 'Assignment to Third Party' },

        // ── Correspondence & Instructions ──
        { ar: 'سري للغاية وعاجل جداً', en: 'Top Secret and Most Urgent' },
        { ar: 'سري للغاية وعاجل', en: 'Top Secret and Urgent' },
        { ar: 'سري وعاجل', en: 'Confidential and Urgent' },
        { ar: 'عاجل وسري', en: 'Urgent and Confidential' },
        { ar: 'سري للغاية', en: 'Top Secret' },
        { ar: 'عاجل جداً', en: 'Most Urgent' },
        { ar: 'سري ومكتوم', en: 'Strictly Confidential' },
        { ar: 'سري', en: 'Confidential' },
        { ar: 'عاجل', en: 'Urgent' },
        { ar: 'وثيقة رسمية صادرة من', en: 'Official document issued by' },
        { ar: 'وثيقة رسمية صادرة عن', en: 'Official document issued by' },
        { ar: 'وثيقة رسمية', en: 'Official document' },
        { ar: 'خطاب رسمي صادر من', en: 'Official letter issued by' },
        { ar: 'خطاب رسمي صادر عن', en: 'Official letter issued by' },
        { ar: 'خطاب رسمي', en: 'Official letter' },
        { ar: 'كتاب رسمي', en: 'Official Letter' },
        { ar: 'يحتوي المستند على', en: 'This document contains' },
        { ar: 'يوثق المستند', en: 'This document records' },
        { ar: 'هذا المستند عبارة عن', en: 'This document is' },
        { ar: 'نرفق لسعادتكم', en: 'Enclosed for Your Excellency' },
        { ar: 'نرفع لسعادتكم', en: 'We submit to Your Excellency' },
        { ar: 'يرجى الحضور إلى', en: 'Kindly report to' },
        { ar: 'يرجى الحضور الى', en: 'Kindly report to' },
        { ar: 'يرجى الحضور', en: 'Kindly report / attend' },
        { ar: 'يرجى مراجعة', en: 'Kindly visit / contact' },
        { ar: 'يرجى مراجعتنا', en: 'Kindly visit our office' },
        { ar: 'يرجى تسليم', en: 'Kindly hand over' },
        { ar: 'يرجى إخلاء', en: 'Kindly vacate' },
        { ar: 'يرجى اخلاء', en: 'Kindly vacate' },
        { ar: 'يرجى سداد', en: 'Kindly settle / pay' },
        { ar: 'يرجى دفع', en: 'Kindly pay' },
        { ar: 'يرجى العلم بأن', en: 'Kindly note that' },
        { ar: 'يرجى التكرم بالعلم', en: 'Kindly be informed' },
        { ar: 'يرجى التكرم بالموافقة', en: 'Kindly approve' },
        { ar: 'يرجى التكرم باتخاذ اللازم', en: 'Kindly take necessary action' },
        { ar: 'نحيطكم علماً بأن', en: 'We hereby inform you that' },
        { ar: 'نود إفادتكم بأن', en: 'We would like to inform you that' },
        { ar: 'نود إفادتكم', en: 'We would like to inform you' },
        { ar: 'للتفضل بالعلم واتخاذ ما يلزم', en: 'For your kind information and necessary action' },
        { ar: 'للتفضل بالعلم', en: 'For your kind information' },
        { ar: 'لاتخاذ ما يلزم', en: 'To take necessary action' },
        { ar: 'لاتخاذ اللازم', en: 'To take necessary action' },
        { ar: 'اتخاذ الإجراءات القانونية', en: 'take legal procedures' },
        { ar: 'سيتم اتخاذ الإجراءات القانونية', en: 'legal action will be taken' },
        { ar: 'الإجراءات القانونية اللازمة', en: 'necessary legal procedures' },
        { ar: 'الإجراءات القانونية', en: 'legal procedures' },
        { ar: 'اتخاذ اللازم', en: 'take necessary action' },
        { ar: 'بالإشارة إلى الموضوع أعلاه', en: 'With reference to the above subject' },
        { ar: 'بالإشارة إلى الموضوع', en: 'With reference to the subject' },
        { ar: 'بالإشارة إلى كتابكم', en: 'With reference to your letter' },
        { ar: 'بالإشارة إلى خطابكم', en: 'With reference to your letter' },
        { ar: 'إشارة إلى الموضوع أعلاه', en: 'With reference to the above subject' },
        { ar: 'إشارة إلى الموضوع', en: 'With reference to the subject' },
        { ar: 'إشارة إلى خطابكم', en: 'With reference to your letter' },
        { ar: 'إشارة إلى كتابكم', en: 'With reference to your letter' },
        { ar: 'استناداً إلى', en: 'Pursuant to' },
        { ar: 'بناءً على طلبكم', en: 'Upon your request' },
        { ar: 'بناءً على ما تقدم', en: 'Based on the foregoing' },
        { ar: 'بناءً على', en: 'Based on / Pursuant to' },
        { ar: 'بناء عليه', en: 'Accordingly' },
        { ar: 'وعليه يرجى', en: 'Accordingly, kindly' },
        { ar: 'وعليه', en: 'Accordingly' },
        { ar: 'وفي حال عدم', en: 'And in the event of failure to' },
        { ar: 'في حال عدم', en: 'In the event of failure to' },
        { ar: 'دون قيد أو شرط', en: 'unconditionally' },
        { ar: 'دون أي تأخير', en: 'without any delay' },
        { ar: 'بدون أي تأخير', en: 'without any delay' },
        { ar: 'في موعد أقصاه', en: 'no later than' },
        { ar: 'خلال مدة أقصاها', en: 'within a maximum period of' },
        { ar: 'خلال أسبوعين', en: 'within two weeks' },
        { ar: 'خلال أسبوع', en: 'within a week' },
        { ar: 'خلال شهر', en: 'within a month' },
        { ar: 'أيام عمل', en: 'working days' },
        { ar: 'يوم عمل', en: 'working day' },
        { ar: 'المذكور أعلاه', en: 'mentioned above' },
        { ar: 'المذكورة أعلاه', en: 'mentioned above' },
        { ar: 'المذكورين أعلاه', en: 'mentioned above' },
        { ar: 'المذكور أدناه', en: 'mentioned below' },
        { ar: 'المذكورة أدناه', en: 'mentioned below' },
        { ar: 'المبين أعلاه', en: 'indicated above' },
        { ar: 'المبين أدناه', en: 'indicated below' },
        { ar: 'الموضح أعلاه', en: 'shown above' },
        { ar: 'الموضح أدناه', en: 'shown below' },
        { ar: 'المشار إليه أعلاه', en: 'referred to above' },
        { ar: 'المشار إليه', en: 'referred to' },
        { ar: 'السالف ذكره', en: 'aforementioned' },
        { ar: 'الكائن في', en: 'located in' },
        { ar: 'الكائنة في', en: 'located in' },
        { ar: 'المرفق طيه', en: 'enclosed herewith' },
        { ar: 'مرفق طيه', en: 'enclosed herewith' },
        { ar: 'طي هذا الكتاب', en: 'enclosed with this letter' },
        { ar: 'شيك مصرفي', en: 'Bank Cheque' },
        { ar: 'تحويل بنكي', en: 'Bank Transfer' },
        { ar: 'تحويل مصرفي', en: 'Bank Transfer' },
        { ar: 'حساب بنكي', en: 'Bank Account' },
        { ar: 'حساب مصرفي', en: 'Bank Account' },
        { ar: 'الموضوع يتضمن', en: 'The subject entails' },
        { ar: 'الموضوع:', en: 'Subject:' },
        { ar: 'الموضوع', en: 'Subject' },
        { ar: 'تحية طيبة وبعد', en: 'Greetings,' },
        { ar: 'السلام عليكم ورحمة الله وبركاته', en: 'Peace and blessings be upon you,' },
        { ar: 'وتفضلوا بقبول فائق الاحترام والتقدير', en: 'Please accept our highest respect and appreciation' },
        { ar: 'وتفضلوا بقبول فائق الاحترام', en: 'Please accept our highest respect' },
        { ar: 'شاكرين حسن تعاونكم', en: 'Thanking you for your cooperation' },
        { ar: 'بخصوص', en: 'regarding' },
        { ar: 'برقم صادر', en: 'with outgoing ref no.' },
        { ar: 'برقم وارد', en: 'with incoming ref no.' },
        { ar: 'برقم قيد', en: 'with registration no.' },
        { ar: 'رقم الصادر', en: 'Outgoing No.' },
        { ar: 'رقم الوارد', en: 'Incoming No.' },
        { ar: 'رقم الملف', en: 'File No.' },
        { ar: 'رقم القيد', en: 'Registration No.' },
        { ar: 'رقم الطلب', en: 'Application No.' },
        { ar: 'رقم الإشعار', en: 'Notice No.' },
        { ar: 'رقم الهاتف', en: 'Phone No.' },
        { ar: 'رقم المبنى', en: 'Building No.' },
        { ar: 'رقم الشقة', en: 'Flat No.' },
        { ar: 'رقم الطريق', en: 'Road No.' },
        { ar: 'رقم المجمع', en: 'Block No.' },
        { ar: 'برقم', en: 'under reference' },
        { ar: 'بتاريخ', en: 'dated' },
        { ar: 'الموافق', en: 'corresponding to' },
        { ar: 'المؤرخ في', en: 'dated' },
        { ar: 'موجه إلى', en: 'addressed to' },
        { ar: 'موجهة إلى', en: 'addressed to' },
        { ar: 'موجهة من', en: 'issued by' },
        { ar: 'موجه من', en: 'issued by' },
        { ar: 'صادر من', en: 'issued from' },
        { ar: 'صادر عن', en: 'issued by' },
        { ar: 'الوحدة السكنية رقم', en: 'Housing Unit No.' },
        { ar: 'الوحدة السكنية', en: 'Housing Unit' },
        { ar: 'وحدة سكنية', en: 'Housing Unit' },
        { ar: 'المسكن رقم', en: 'House No.' },
        { ar: 'مسكن رقم', en: 'House No.' },
        { ar: 'مسكن', en: 'Residence' },
        { ar: 'شقة رقم', en: 'Flat No.' },
        { ar: 'مبنى رقم', en: 'Building No.' },
        { ar: 'طريق رقم', en: 'Road No.' },
        { ar: 'مجمع رقم', en: 'Block No.' },
        { ar: 'منطقة سافرة', en: 'Safra Area' },
        { ar: 'منطقة سافر', en: 'Safra Area' },
        { ar: 'منطقة مسافر', en: 'Saafer Area' },
        { ar: 'منطقة عوالي', en: 'Awali Area' },
        { ar: 'منطقة الرفاع', en: 'Riffa Area' },
        { ar: 'الرفاع الغربي', en: 'West Riffa' },
        { ar: 'الرفاع الشرقي', en: 'East Riffa' },
        { ar: 'مدينة عيسى', en: 'Isa Town' },
        { ar: 'مدينة حمد', en: 'Hamad Town' },
        { ar: 'مدينة سلمان', en: 'Salman City' },
        { ar: 'مدينة زايد', en: 'Zayed Town' },
        { ar: 'المنامة', en: 'Manama' },
        { ar: 'المحرق', en: 'Muharraq' },
        { ar: 'منطقة', en: 'Area' },
        { ar: 'مجمع', en: 'Block' },
        { ar: 'طريق', en: 'Road' },
        { ar: 'شارع', en: 'Avenue' },
        { ar: 'توقيع', en: 'Signature' },
        { ar: 'ختم', en: 'Official Stamp' },
        { ar: 'اعتماد', en: 'Approval' },
        { ar: 'مرفقات', en: 'Attachments' },
        { ar: 'نسخة إلى', en: 'Copy to' },
        { ar: 'صورة إلى', en: 'Copy to' },
        { ar: 'إقرار', en: 'Declaration' },
        { ar: 'الجنسية', en: 'Nationality' },
        { ar: 'بحريني', en: 'Bahraini' },
        { ar: 'بحرينية', en: 'Bahraini (F)' },
        { ar: 'غير بحريني', en: 'Non-Bahraini' },
        { ar: 'الحالة الاجتماعية', en: 'Marital Status' },
        { ar: 'متزوج', en: 'Married' },
        { ar: 'أعزب', en: 'Single' },
        { ar: 'مطلق', en: 'Divorced' },
        { ar: 'أرمل', en: 'Widowed' },
        { ar: 'المهنة', en: 'Occupation' },
        { ar: 'جهة العمل', en: 'Employer' },
        { ar: 'الرتبة العسكرية', en: 'Military Rank' },
        { ar: 'الرقم العسكري', en: 'Military ID No.' },
        { ar: 'الرتبة', en: 'Rank' },
        { ar: 'فريق أول', en: 'General' },
        { ar: 'فريق', en: 'Lieutenant General' },
        { ar: 'لواء', en: 'Major General' },
        { ar: 'عميد', en: 'Brigadier' },
        { ar: 'العقيد', en: 'Colonel' },
        { ar: 'عقيد', en: 'Colonel' },
        { ar: 'المقدم', en: 'Lieutenant Colonel' },
        { ar: 'مقدم', en: 'Lieutenant Colonel' },
        { ar: 'الرائد', en: 'Major' },
        { ar: 'رائد', en: 'Major' },
        { ar: 'النقيب', en: 'Captain' },
        { ar: 'نقيب', en: 'Captain' },
        { ar: 'ملازم أول', en: 'First Lieutenant' },
        { ar: 'ملازم ثاني', en: 'Second Lieutenant' },
        { ar: 'ملازم متقاعد', en: 'Retired Lieutenant' },
        { ar: 'ملازم', en: 'Lieutenant' },
        { ar: 'وكيل أول', en: 'Senior Warrant Officer' },
        { ar: 'وكيل ضابط', en: 'Warrant Officer' },
        { ar: 'رقيب أول', en: 'Master Sergeant' },
        { ar: 'رقيب', en: 'Sergeant' },
        { ar: 'العريف', en: 'Corporal' },
        { ar: 'عريف', en: 'Corporal' },
        { ar: 'شرطي أول', en: 'First Constable' },
        { ar: 'شرطي', en: 'Constable' },
        { ar: 'مدني', en: 'Civilian' },
        { ar: 'متقاعد', en: 'Retired' },
        { ar: 'مدير عام', en: 'Director General' },
        { ar: 'مدير إدارة', en: 'Director of' },
        { ar: 'مدير مكتب', en: 'Director of the Office of' },
        { ar: 'مدير', en: 'Director' },
        { ar: 'رئيس فرع', en: 'Head of Branch' },
        { ar: 'رئيس قسم', en: 'Head of Section' },
        { ar: 'رئيس', en: 'Head' },
        { ar: 'مقرر اللجنة', en: 'Committee Rapporteur' },
        { ar: 'مقرر', en: 'Rapporteur' },
        { ar: 'الباحث القانوني', en: 'Legal Researcher' },
        { ar: 'باحث قانوني', en: 'Legal Researcher' },
        { ar: 'المستشار القانوني', en: 'Legal Advisor' },
        { ar: 'أخصائي إسكان', en: 'Housing Specialist' },
        { ar: 'مهندس', en: 'Engineer' },
        { ar: 'سعادة', en: 'His Excellency' },
        { ar: 'معالي', en: 'His Excellency (Minister)' },
        { ar: 'معاليكم', en: 'Your Excellency' },
        { ar: 'المحترم', en: 'Esq.' },
        { ar: 'المحترمين', en: 'Respected' },
        { ar: 'السيد', en: 'Mr.' },
        { ar: 'السيدة', en: 'Mrs.' },
        { ar: 'دينار بحريني', en: 'Bahraini Dinar (BHD)' },
        { ar: 'دينار', en: 'BHD' },
        { ar: 'فلساً', en: 'Fils' },
        { ar: 'فلس', en: 'Fils' },
        { ar: 'شهرياً', en: 'Monthly' },
        { ar: 'سنوياً', en: 'Annually' },

        // ── Common Administrative, Notice & Legal Phrases ──
        { ar: 'بسم الله الرحمن الرحيم', en: 'In the name of Allah/God, the Most Gracious, the Most Merciful' },
        { ar: 'يرجى التكرم بالحضور', en: 'Kindly attend / report in person' },
        { ar: 'يرجى التكرم بالعلم', en: 'Kindly be informed' },
        { ar: 'نحيطكم علماً بأن', en: 'We hereby inform you that' },
        { ar: 'نحيطكم علماً', en: 'We hereby inform you' },
        { ar: 'بناء على ما تقدم', en: 'Based on the foregoing' },
        { ar: 'بناءً على ما تقدم', en: 'Based on the foregoing' },
        { ar: 'قيد الدراسة', en: 'under review / pending' },
        { ar: 'قيد التنفيذ', en: 'in progress / under implementation' },
        { ar: 'المعمول بها', en: 'applicable / in force' },
        { ar: 'المعمول به', en: 'applicable / in force' },
        { ar: 'البطاقة الذكية', en: 'Smart Card / National ID' },
        { ar: 'بطاقة ذكية', en: 'Smart Card / National ID' },
        { ar: 'كشف حساب بنكي', en: 'Bank Account Statement' },
        { ar: 'كشف حساب', en: 'Account Statement' },
        { ar: 'رقم الحساب الدولي الآيبان', en: 'IBAN (International Bank Account Number)' },
        { ar: 'رقم الحساب الدولي', en: 'IBAN (International Bank Account Number)' },
        { ar: 'الحساب الدولي الآيبان', en: 'IBAN (International Bank Account Number)' },
        { ar: 'الحساب الدولي', en: 'International Account (IBAN)' },
        { ar: 'الطرف الأول: المؤجر', en: 'First Party: Lessor / Landlord' },
        { ar: 'الطرف الثاني: المستأجر', en: 'Second Party: Tenant' },
        { ar: 'الطرف الأول', en: 'First Party (Lessor)' },
        { ar: 'الطرف الثاني', en: 'Second Party (Tenant)' },
        { ar: 'مدة العقد', en: 'Contract Duration' },
        { ar: 'سنة واحدة', en: 'One Year' },
        { ar: 'والقيمة الإيجارية الشهرية', en: 'and the Monthly Rental Amount' },
        { ar: 'القيمة الإيجارية الشهرية', en: 'Monthly Rental Amount' },
        { ar: 'والقيمة الإيجارية', en: 'and the Rental Value' },
        { ar: 'القيمة الإيجارية', en: 'Rental Value' },
        { ar: 'الأجرة المستحقة', en: 'Outstanding Rent Due' },
        { ar: 'الأجرة الشهرية', en: 'Monthly Rent' },
        { ar: 'إشعار إخلاء', en: 'Eviction Notice' },
        { ar: 'إنذار إخلاء', en: 'Eviction Warning' },
        { ar: 'أمر إخلاء', en: 'Eviction Order' },
        { ar: 'شعبة الإسكان', en: 'Housing Division' },
        { ar: 'قسم الشؤون القانونية', en: 'Legal Affairs Department' },
        { ar: 'قسم الشئون القانونية', en: 'Legal Affairs Department' },
        { ar: 'الشؤون القانونية', en: 'Legal Affairs' },
        { ar: 'الشئون القانونية', en: 'Legal Affairs' },
        { ar: 'خلال مدة أقصاها', en: 'within a maximum period of' },
        { ar: 'أيام من تاريخه', en: 'days from its date' },
        { ar: 'من تاريخه', en: 'from its date' },
        { ar: 'اتخاذ الإجراءات القانونية', en: 'initiating legal proceedings' },
        { ar: 'الإجراءات القانونية', en: 'legal procedures' },
        { ar: 'بحالة جيدة', en: 'in good condition' },
        { ar: 'خالية من الشواغل', en: 'vacant and free of encumbrances' },
        { ar: 'الكهرباء والماء', en: 'Electricity and Water' },
        { ar: 'فواتير الكهرباء والماء', en: 'Electricity & Water Bills' },
        { ar: 'فواتير الكهرباء', en: 'Electricity Bills' },
        { ar: 'الختم الرسمي', en: 'Official Stamp / Seal' },
        { ar: 'تحريراً في', en: 'Issued on / Executed on' },
        { ar: 'تبدأ من', en: 'commencing from' },
        { ar: 'وتنتهي في', en: 'and expiring on' },
        { ar: 'تنتهي في', en: 'expiring on' },
        { ar: 'تم استلام', en: 'has been received' },
        { ar: 'وفقاً للأنظمة واللوائح', en: 'in accordance with systems and regulations' },
        { ar: 'وفقاً للأنظمة', en: 'in accordance with regulations' },
        { ar: 'إدارة الخدمات الإسكانية', en: 'Housing Services Directorate' },
        { ar: 'صيانة وإصلاح', en: 'Maintenance & Repair' },
        { ar: 'طلب صيانة', en: 'Maintenance Request' },
        { ar: 'توقيع المستأجر', en: 'Tenant Signature' },
        { ar: 'توقيع المؤجر', en: 'Lessor Signature' },
        { ar: 'الرقم الشخصي', en: 'CPR / ID Number' },
        { ar: 'مقر الوزارة', en: 'Ministry Headquarters' },
        { ar: 'مقر شعبة', en: 'Division Headquarters' },
        { ar: 'إلى مقر', en: 'to the headquarters of' },
        { ar: 'التكرم بالحضور', en: 'kindly attend / report' },
        { ar: 'لعدم سداد', en: 'for non-payment of' }
    ];

    // ── Word-Level Vocabulary Dictionary (500+ Words) ──
    const ARABIC_WORDS = {
        // Days & Months
        'الاحد': 'Sunday', 'الأحد': 'Sunday', 'الاثنين': 'Monday', 'الإثنين': 'Monday',
        'الثلاثاء': 'Tuesday', 'الاربعاء': 'Wednesday', 'الأربعاء': 'Wednesday',
        'الخميس': 'Thursday', 'الجمعة': 'Friday', 'السبت': 'Saturday',
        'يوم': 'Day', 'ايام': 'Days', 'أيام': 'Days',
        'يناير': 'January', 'فبراير': 'February', 'مارس': 'March', 'ابريل': 'April', 'أبريل': 'April',
        'مايو': 'May', 'يونيو': 'June', 'يوليو': 'July', 'اغسطس': 'August', 'أغسطس': 'August',
        'سبتمبر': 'September', 'اكتوبر': 'October', 'أكتوبر': 'October', 'نوفمبر': 'November', 'ديسمبر': 'December',
        'شهر': 'Month', 'شهري': 'Monthly', 'شهور': 'Months', 'اشهر': 'Months', 'أشهر': 'Months',
        'سنة': 'Year', 'سنوي': 'Annual', 'سنوات': 'Years', 'عام': 'Year', 'اعوام': 'Years', 'أعوام': 'Years',

        // Housing & Property
        'بيت': 'House', 'بيوت': 'Houses', 'منزل': 'Home', 'منازل': 'Homes', 'دار': 'Residence',
        'مسكن': 'Residence', 'مساكن': 'Residences', 'المسكن': 'Residence', 'سكن': 'Housing', 'سكني': 'Residential', 'سكنية': 'Residential',
        'شقة': 'Flat', 'شقق': 'Apartments', 'مبنى': 'Building', 'مباني': 'Buildings', 'المبنى': 'Building', 'عمارة': 'Building',
        'وحدة': 'Unit', 'وحدات': 'Units', 'الوحدة': 'Unit', 'عقار': 'Property', 'عقارات': 'Properties', 'العقار': 'Property',
        'قسيمة': 'Plot', 'قسائم': 'Plots', 'ارض': 'Land', 'أرض': 'Land', 'اراضي': 'Lands', 'أراضي': 'Lands',
        'غرفة': 'Room', 'غرف': 'Rooms', 'صالة': 'Hall', 'مطبخ': 'Kitchen', 'حمام': 'Bathroom', 'دورات': 'Bathrooms',
        'كراج': 'Garage', 'موقف': 'Parking', 'مواقف': 'Parking lots', 'حديقة': 'Garden', 'سطح': 'Roof', 'سقف': 'Ceiling',
        'درج': 'Stairs', 'مدخل': 'Entrance', 'مخرج': 'Exit', 'باب': 'Door', 'ابواب': 'Doors', 'أبواب': 'Doors',
        'نافذة': 'Window', 'نوافذ': 'Windows', 'مفتاح': 'Key', 'مفاتيح': 'Keys', 'المفتاح': 'Key', 'المفاتيح': 'Keys',
        'قفل': 'Lock', 'اقفال': 'Locks', 'أقفال': 'Locks', 'جدار': 'Wall', 'جدران': 'Walls', 'سور': 'Fence / Wall',
        'ارضية': 'Floor', 'أرضية': 'Floor', 'ارضيات': 'Floors', 'أرضيات': 'Floors', 'بلاط': 'Tiles', 'صبغ': 'Paint', 'اصباغ': 'Paints', 'أصباغ': 'Paints',

        // Contract & Law
        'عقد': 'Contract', 'العقد': 'Contract', 'عقود': 'Contracts', 'اتفاق': 'Agreement', 'اتفاقية': 'Agreement',
        'طرف': 'Party', 'الطرف': 'Party', 'اطراف': 'Parties', 'أطراف': 'Parties', 'طرفان': 'Both Parties', 'الطرفان': 'Both Parties',
        'مؤجر': 'Lessor', 'المؤجر': 'Lessor', 'مستأجر': 'Tenant', 'المستأجر': 'Tenant', 'مستأجرين': 'Tenants',
        'ايجار': 'Rent', 'إيجار': 'Rent', 'الإيجار': 'Rent', 'الايجار': 'Rent', 'اجرة': 'Rent Fee', 'أجرة': 'Rent Fee', 'الأجرة': 'Rent Fee',
        'بدل': 'Allowance', 'البدل': 'Allowance', 'تأمين': 'Security Deposit', 'تامين': 'Security Deposit', 'التأمين': 'Security Deposit',
        'استقطاع': 'Deduction', 'استقطاعات': 'Deductions', 'الاستقطاع': 'Deduction',
        'قيمة': 'Value', 'القيمة': 'Value', 'مبلغ': 'Amount', 'المبلغ': 'Amount', 'مبالغ': 'Amounts', 'رصيد': 'Balance', 'الرصيد': 'Balance', 'حساب': 'Account', 'الحساب': 'Account',
        'شرط': 'Condition', 'الشرط': 'Condition', 'شروط': 'Terms', 'الشروط': 'Terms', 'بند': 'Clause', 'البند': 'Clause', 'بنود': 'Clauses', 'البنود': 'Clauses',
        'مادة': 'Article', 'المادة': 'Article', 'مواد': 'Articles', 'المواد': 'Articles', 'فقرة': 'Paragraph',
        'قانون': 'Law', 'القانون': 'Law', 'قوانين': 'Laws', 'نظام': 'Regulation', 'النظام': 'Regulation', 'أنظمة': 'Regulations', 'انظمة': 'Regulations',
        'لائحة': 'Bylaw', 'اللائحة': 'Bylaw', 'لوائح': 'Bylaws', 'قرار': 'Decision', 'القرار': 'Decision', 'قرارات': 'Decisions',
        'اوامر': 'Orders', 'أوامر': 'Orders', 'امر': 'Order', 'أمر': 'Order', 'الأمر': 'Order',
        'التزام': 'Obligation', 'التزامات': 'Obligations', 'تعهد': 'Undertaking', 'تعهدات': 'Undertakings', 'التعهد': 'Undertaking',
        'اخلاء': 'Eviction', 'إخلاء': 'Eviction', 'الإخلاء': 'Eviction', 'تسليم': 'Handover', 'التسليم': 'Handover', 'استلام': 'Receipt', 'الاستلام': 'Receipt',
        'صيانة': 'Maintenance', 'الصيانة': 'Maintenance', 'اصلاح': 'Repair', 'إصلاح': 'Repair', 'الإصلاح': 'Repair', 'ترميم': 'Renovation', 'الترميم': 'Renovation',
        'تخصيص': 'Allocation', 'التخصيص': 'Allocation', 'انتفاع': 'Occupancy', 'الانتفاع': 'Occupancy',
        'مستفيد': 'Beneficiary', 'المستفيد': 'Beneficiary', 'مستفيدين': 'Beneficiaries', 'المستفيدين': 'Beneficiaries',
        'فسخ': 'Termination', 'انهاء': 'Termination', 'إنهاء': 'Termination', 'الإنهاء': 'Termination',
        'تجديد': 'Renewal', 'التجديد': 'Renewal', 'تمديد': 'Extension', 'التمديد': 'Extension',
        'سريان': 'Validity', 'صلاحية': 'Validity', 'انتهاء': 'Expiry', 'الانتهاء': 'Expiry',
        'مهلة': 'Grace Period', 'فترة': 'Period', 'الفترة': 'Period', 'مدة': 'Duration', 'المدة': 'Duration',
        'غرامة': 'Penalty Fee', 'الغرامة': 'Penalty Fee', 'تاخير': 'Delay', 'تأخير': 'Delay', 'التأخير': 'Delay',
        'مخالفة': 'Violation', 'المخالفة': 'Violation', 'مخالفات': 'Violations', 'المخالفات': 'Violations',
        'ضرر': 'Damage', 'الضرر': 'Damage', 'اضرار': 'Damages', 'أضرار': 'Damages', 'تلف': 'Damage',
        'مسؤولية': 'Responsibility', 'المسؤولية': 'Responsibility', 'مسئولية': 'Responsibility',
        'حظر': 'Prohibition', 'منع': 'Prohibition', 'سماح': 'Permission', 'تصريح': 'Permit', 'تنازل': 'Waiver',
        'طرد': 'Eviction', 'حجز': 'Seizure', 'استرداد': 'Refund / Recovery', 'تعويض': 'Compensation',

        // Official Documents & Correspondence
        'وثيقة': 'Document', 'الوثيقة': 'Document', 'وثائق': 'Documents', 'مستند': 'Document', 'المستند': 'Document', 'مستندات': 'Documents', 'المستندات': 'Documents',
        'خطاب': 'Letter', 'الخطاب': 'Letter', 'كتاب': 'Official Letter', 'الكتاب': 'Official Letter', 'رسالة': 'Letter',
        'اشعار': 'Notice', 'إشعار': 'Notice', 'الإشعار': 'Notice', 'اشعارات': 'Notices', 'إشعارات': 'Notices',
        'انذار': 'Warning', 'إنذار': 'Warning', 'الإنذار': 'Warning', 'انذارات': 'Warnings', 'إنذارات': 'Warnings',
        'اخطار': 'Notification', 'إخطار': 'Notification', 'تنبيه': 'Alert / Warning',
        'محضر': 'Minutes / Record', 'المحضر': 'Record', 'محاضر': 'Records', 'تقرير': 'Report', 'التقرير': 'Report', 'تقارير': 'Reports',
        'كشف': 'Statement', 'الكشف': 'Statement', 'بيان': 'Declaration / Statement', 'البيان': 'Statement', 'بيانات': 'Data / Information', 'البيانات': 'Data',
        'استمارة': 'Form', 'الاستمارة': 'Form', 'نموذج': 'Form', 'النموذج': 'Form', 'نماذج': 'Forms',
        'طلب': 'Application', 'الطلب': 'Application', 'طلبات': 'Applications', 'الطلبات': 'Applications',
        'شهادة': 'Certificate', 'الشهادة': 'Certificate', 'شهادات': 'Certificates', 'رخصة': 'Permit', 'الرخصة': 'Permit',
        'بطاقة': 'Card', 'البطاقة': 'Card', 'هوية': 'Identity', 'الهوية': 'Identity', 'جواز': 'Passport', 'الجواز': 'Passport',
        'رقم': 'No.', 'الرقم': 'No.', 'ارقام': 'Numbers', 'أرقام': 'Numbers', 'الأرقام': 'Numbers',
        'قيد': 'Registration', 'القيد': 'Registration', 'ملف': 'File', 'الملف': 'File', 'ملفات': 'Files',
        'صادر': 'Outgoing', 'الصادر': 'Outgoing', 'وارد': 'Incoming', 'الوارد': 'Incoming',
        'تاريخ': 'Date', 'التاريخ': 'Date', 'تواريخ': 'Dates', 'مرجع': 'Reference', 'المرجع': 'Reference',
        'توقيع': 'Signature', 'التوقيع': 'Signature', 'توقيعات': 'Signatures', 'ختم': 'Stamp', 'الختم': 'Stamp', 'اختام': 'Stamps', 'أختام': 'Stamps',
        'بصمة': 'Fingerprint', 'البصمة': 'Fingerprint', 'اعتماد': 'Approval', 'الاعتماد': 'Approval',
        'موافقة': 'Approval', 'الموافقة': 'Approval', 'رفض': 'Rejection', 'قبول': 'Acceptance',
        'مرفق': 'Attachment', 'المرفق': 'Attachment', 'مرفقات': 'Attachments', 'المرفقات': 'Attachments',
        'مرفقة': 'Attached', 'المرفقة': 'Attached', 'نسخة': 'Copy', 'النسخة': 'Copy', 'صورة': 'Copy', 'الصورة': 'Copy',
        'اصل': 'Original', 'أصل': 'Original', 'الأصل': 'Original',
        'حضور': 'Appearance / Attendance', 'الحضور': 'Attendance / Reporting',
        'مراجعة': 'Visit / Review', 'المراجعة': 'Visit / Review',
        'ضرورة': 'Urgency / Necessity', 'ضروري': 'Necessary', 'نهائي': 'Final', 'نهائية': 'Final', 'نهائيا': 'Finally', 'نهائياً': 'Finally',
        'كائن': 'Located', 'الكائن': 'Located', 'كائنة': 'Located', 'الكائنة': 'Located',
        'مذكور': 'Mentioned', 'المذكور': 'Mentioned', 'مذكورة': 'Mentioned', 'المذكورة': 'Mentioned', 'مذكورين': 'Mentioned', 'المذكورين': 'Mentioned',
        'اعلاه': 'Above', 'أعلاه': 'Above', 'ادناه': 'Below', 'أدناه': 'Below', 'سالف': 'Aforementioned', 'السالف': 'Aforementioned',
        'مبين': 'Indicated', 'المبين': 'Indicated', 'موضح': 'Shown', 'الموضح': 'Shown', 'مشار': 'Referred', 'المشار': 'Referred',
        'اجراء': 'Procedure', 'إجراء': 'Procedure', 'الإجراء': 'Procedure', 'اجراءات': 'Procedures', 'إجراءات': 'Procedures', 'الإجراءات': 'Procedures',
        'لازم': 'Necessary', 'اللازم': 'Necessary', 'لازمة': 'Necessary', 'اللازمة': 'Necessary',
        'طي': 'Enclosed', 'طيه': 'Herewith',
        'انتظام': 'Regularity', 'بانتظام': 'Regularly',

        // Government & Civil
        'مملكة': 'Kingdom', 'المملكة': 'Kingdom', 'دولة': 'State', 'الدولة': 'State', 'حكومة': 'Government', 'الحكومة': 'Government',
        'وزارة': 'Ministry', 'الوزارة': 'Ministry', 'وزارات': 'Ministries',
        'ادارة': 'Directorate', 'إدارة': 'Directorate', 'الإدارة': 'Directorate', 'الادارة': 'Directorate',
        'فرع': 'Branch', 'الفرع': 'Branch', 'فروع': 'Branches', 'قسم': 'Section', 'القسم': 'Section', 'اقسام': 'Sections', 'أقسام': 'Sections',
        'شعبة': 'Division', 'الشعبة': 'Division', 'لجنة': 'Committee', 'اللجنة': 'Committee', 'لجان': 'Committees',
        'هيئة': 'Authority', 'الهيئة': 'Authority', 'مجلس': 'Council', 'المجلس': 'Council',
        'ديوان': 'Court / Bureau', 'الديوان': 'Bureau', 'محكمة': 'Court', 'المحكمة': 'Court',
        'قضاء': 'Judiciary', 'القضاء': 'Judiciary', 'نيابة': 'Prosecution', 'النيابة': 'Prosecution',
        'شرطة': 'Police', 'الشرطة': 'Police', 'امن': 'Security', 'أمن': 'Security', 'الأمن': 'Security',
        'دفاع': 'Defence', 'الدفاع': 'Defence', 'حرس': 'Guard', 'الحرس': 'Guard', 'جيش': 'Army', 'الجيش': 'Army',
        'عسكري': 'Military', 'العسكري': 'Military', 'مدني': 'Civilian', 'المدني': 'Civilian',
        'موظف': 'Employee', 'الموظف': 'Employee', 'موظفين': 'Employees', 'الموظفين': 'Employees',
        'ضابط': 'Officer', 'الضابط': 'Officer', 'ضباط': 'Officers', 'الضباط': 'Officers',
        'رتبة': 'Rank', 'الرتبة': 'Rank', 'رتب': 'Ranks', 'الرتب': 'Ranks',
        'رئيس': 'Head', 'الرئيس': 'Head', 'مدير': 'Director', 'المدير': 'Director',
        'وكيل': 'Undersecretary', 'الوكيل': 'Undersecretary', 'وزير': 'Minister', 'الوزير': 'Minister',
        'مقرر': 'Rapporteur', 'المقرر': 'Rapporteur', 'باحث': 'Researcher', 'الباحث': 'Researcher',
        'مستشار': 'Advisor', 'المستشار': 'Advisor', 'مهندس': 'Engineer', 'المهندس': 'Engineer',
        'اخصائي': 'Specialist', 'أخصائي': 'Specialist', 'الأخصائي': 'Specialist',
        'خدمة': 'Service', 'الخدمة': 'Service', 'خدمات': 'Services', 'الخدمات': 'Services',
        'اسكان': 'Housing', 'إسكان': 'Housing', 'الإسكان': 'Housing',

        // Location & Geography
        'منطقة': 'Area', 'المنطقة': 'Area', 'مناطق': 'Areas', 'محافظة': 'Governorate', 'المحافظة': 'Governorate', 'بلدية': 'Municipality', 'البلدية': 'Municipality',
        'مدينة': 'City', 'المدينة': 'City', 'قرية': 'Village', 'القرية': 'Village',
        'مجمع': 'Block', 'المجمع': 'Block', 'طريق': 'Road', 'الطريق': 'Road', 'شارع': 'Avenue', 'الشارع': 'Avenue',
        'جنوبية': 'Southern', 'شمالية': 'Northern', 'عاصمة': 'Capital', 'وسطى': 'Central',
        'سافرة': 'Safra', 'سافر': 'Safra', 'عوالي': 'Awali', 'رفاع': 'Riffa', 'الرفاع': 'Riffa', 'منامة': 'Manama', 'المنامة': 'Manama', 'محرق': 'Muharraq', 'المحرق': 'Muharraq',

        // Financial & Utilities
        'كهرباء': 'Electricity', 'الكهرباء': 'Electricity', 'ماء': 'Water', 'الماء': 'Water', 'مياه': 'Water', 'المياه': 'Water',
        'استهلاك': 'Consumption', 'الاستهلاك': 'Consumption', 'فاتورة': 'Bill', 'الفاتورة': 'Bill', 'فواتير': 'Bills',
        'عداد': 'Meter', 'العداد': 'Meter', 'قراءة': 'Reading', 'القراءة': 'Reading',
        'سداد': 'Payment', 'السداد': 'Payment', 'دفع': 'Payment', 'الدفع': 'Payment',
        'مدفوع': 'Paid', 'مستحق': 'Due', 'المستحق': 'Due', 'متأخرات': 'Arrears', 'المتأخرات': 'Arrears', 'متاخرات': 'Arrears',
        'تحصيل': 'Collection', 'التحصيل': 'Collection', 'قسط': 'Installment', 'القسط': 'Installment', 'اقساط': 'Installments', 'أقساط': 'Installments',
        'بنك': 'Bank', 'البنك': 'Bank', 'بنوك': 'Banks', 'مصرف': 'Bank', 'المصرف': 'Bank',
        'شيك': 'Cheque', 'الشيك': 'Cheque', 'شيكات': 'Cheques', 'الشيكات': 'Cheques',
        'راتب': 'Salary', 'الراتب': 'Salary', 'رواتب': 'Salaries',
        'دينار': 'Dinar', 'الدينار': 'Dinar', 'دنانير': 'Dinars', 'فلس': 'Fils', 'الفلس': 'Fils',
        'اجمالي': 'Total', 'إجمالي': 'Total', 'الإجمالي': 'Total', 'صافي': 'Net', 'الصافي': 'Net', 'مجموع': 'Total', 'المجموع': 'Total',
        'متبقي': 'Remaining', 'المتبقي': 'Remaining', 'باقي': 'Remaining',

        // Verbs & Particles
        'يرجى': 'Kindly', 'نرجو': 'We request', 'رجاء': 'Please', 'الرجاء': 'Please',
        'يلتزم': 'undertakes', 'يتعهد': 'pledges', 'يقر': 'declares', 'يوافق': 'agrees',
        'يدفع': 'pays', 'يسدد': 'settles', 'يستلم': 'receives', 'يسلم': 'hands over',
        'يخلي': 'vacates', 'يحافظ': 'preserves', 'يخطر': 'notifies', 'ينذر': 'warns',
        'يوقع': 'signs', 'يعتمد': 'approves', 'يعتبر': 'is considered', 'يجوز': 'may', 'يحظر': 'is prohibited',
        'يجب': 'shall', 'ينبغي': 'should', 'يتعين': 'is required', 'يلزم': 'is required',
        'يراجع': 'reviews / visits', 'يحضر': 'reports / attends', 'يخالف': 'violates',
        'تم': 'completed', 'صدر': 'issued', 'ورد': 'received',
        'في': 'in', 'على': 'on', 'إلى': 'to', 'الى': 'to', 'من': 'from', 'عن': 'about',
        'مع': 'with', 'بين': 'between', 'لدى': 'with', 'حتى': 'until', 'منذ': 'since',
        'بعد': 'after', 'قبل': 'before', 'تحت': 'under', 'فوق': 'above', 'امام': 'in front of', 'أمام': 'in front of',
        'خلف': 'behind', 'داخل': 'inside', 'خارج': 'outside', 'خلال': 'during',
        'هذا': 'this', 'هذه': 'this', 'ذلك': 'that', 'تلك': 'that', 'هؤلاء': 'these',
        'هو': 'he', 'هي': 'she', 'هم': 'they', 'نحن': 'we', 'انا': 'I', 'أنا': 'I',
        'الذي': 'which', 'التي': 'which', 'الذين': 'who',
        'كل': 'every', 'جميع': 'all', 'كافة': 'all', 'بعض': 'some', 'غير': 'non / other', 'دون': 'without', 'بدون': 'without',
        'فقط': 'only', 'ايضا': 'also', 'أيضاً': 'also', 'كذلك': 'likewise',
        'حسب': 'according to', 'وفق': 'according to', 'بموجب': 'pursuant to', 'بناء': 'based',
        'الاول': 'First', 'الأول': 'First', 'اول': 'first', 'أول': 'first', 'اولى': 'First', 'أولى': 'First',
        'الثاني': 'Second', 'ثاني': 'second', 'ثانية': 'Second',
        'الثالث': 'Third', 'ثالث': 'third',
        'الرابع': 'Fourth', 'رابع': 'fourth',
        'الخامس': 'Fifth', 'خامس': 'fifth',
        'السادس': 'Sixth', 'سادس': 'sixth',
        'السابع': 'Seventh', 'سابع': 'seventh',
        'الثامن': 'Eighth', 'ثامن': 'eighth',
        'التاسع': 'Ninth', 'تاسع': 'ninth',
        'العاشر': 'Tenth', 'عاشر': 'tenth',
        'كامل': 'full', 'الكامل': 'full', 'شامل': 'comprehensive', 'عام': 'general', 'خاص': 'special',

        // Common sentence particles & connectors
        'حيث': 'where / whereas', 'بحيث': 'such that', 'لذا': 'therefore', 'لذلك': 'therefore',
        'إذا': 'if', 'اذا': 'if', 'لو': 'if', 'إذ': 'since / as', 'اذ': 'since / as',
        'لكن': 'but', 'ولكن': 'however', 'إلا': 'except', 'الا': 'except', 'سوى': 'except',
        'أو': 'or', 'او': 'or', 'ام': 'or', 'أم': 'or',
        'أن': 'that', 'ان': 'that', 'إن': 'indeed', 'ان': 'that',
        'لا': 'no / not', 'لم': 'did not', 'لن': 'will not', 'ما': 'what / not', 'ليس': 'is not',
        'قد': 'may / has', 'سوف': 'shall / will',
        'عند': 'at / when', 'حين': 'when', 'عندما': 'when',
        'كما': 'as / also', 'مثل': 'like', 'كي': 'in order to', 'لأن': 'because', 'لان': 'because',
        'منها': 'including', 'بينها': 'among them', 'عليها': 'on it', 'فيها': 'in it', 'منه': 'from it',
        'له': 'for him', 'لها': 'for her/it', 'لهم': 'for them',
        'عليه': 'on him / upon which', 'فيه': 'in it / therein',
        'ذات': 'of / same', 'نفس': 'same', 'كلا': 'both', 'كلتا': 'both',
        'ضمن': 'within', 'حول': 'about / around', 'تجاه': 'towards', 'نحو': 'towards / about',
        'ثم': 'then', 'أيضا': 'also', 'بل': 'rather', 'حتي': 'until',
        'ابتداء': 'starting', 'اعتبارا': 'effective', 'اعتباراً': 'effective',
        'وفقا': 'according to', 'وفقاً': 'according to', 'طبقا': 'in accordance with', 'طبقاً': 'in accordance with',
        'نظرا': 'given that', 'نظراً': 'given that', 'استنادا': 'based on', 'استناداً': 'based on',
        'علما': 'noting that', 'علماً': 'noting that',

        // Subject / Topic / Content  
        'موضوع': 'Subject', 'الموضوع': 'Subject', 'مضمون': 'Content', 'المضمون': 'Content',
        'شأن': 'Regard', 'الشأن': 'Regard', 'بشأن': 'Regarding', 'بخصوص': 'Regarding',
        'خصوص': 'Regard', 'الخصوص': 'Regard',
        'سبب': 'Reason', 'السبب': 'Reason', 'اسباب': 'Reasons', 'أسباب': 'Reasons',
        'هدف': 'Objective', 'الهدف': 'Objective', 'اهداف': 'Objectives', 'أهداف': 'Objectives',
        'غرض': 'Purpose', 'الغرض': 'Purpose', 'اغراض': 'Purposes', 'أغراض': 'Purposes',
        'نتيجة': 'Result', 'النتيجة': 'Result', 'نتائج': 'Results',

        // Religious / opening phrases
        'بسم': 'In the name of', 'الله': 'Allah/God', 'الرحمن': 'the Most Gracious',
        'الرحيم': 'the Most Merciful', 'الحمد': 'Praise', 'رب': 'Lord',
        'صلاة': 'Prayer', 'سلام': 'Peace', 'السلام': 'Peace',

        // Verbs & Actions (additional)
        'يمنح': 'grants', 'يمنع': 'prohibits', 'يكون': 'is/shall be', 'تكون': 'is/shall be',
        'يتم': 'is done', 'يعد': 'is considered', 'تعد': 'is considered',
        'يقوم': 'carries out', 'تقوم': 'carries out',
        'يطلب': 'requests', 'يبلغ': 'notifies', 'يخالف': 'violates',
        'يتقدم': 'applies', 'يستحق': 'deserves / is due',
        'يحق': 'has the right', 'يتضمن': 'includes', 'يشمل': 'includes',
        'يتعلق': 'relates to', 'يخص': 'concerns', 'يتطلب': 'requires',
        'يؤكد': 'confirms', 'يعلم': 'knows / notifies', 'يفيد': 'informs / states',
        'يثبت': 'proves', 'ينص': 'stipulates', 'يقضي': 'rules / decides',
        'يتوجب': 'must', 'يستوجب': 'necessitates',
        'يبدأ': 'begins', 'ينتهي': 'ends', 'يستمر': 'continues',
        'يؤدي': 'leads to', 'ينتج': 'results in',
        'يرفض': 'rejects', 'يقبل': 'accepts', 'يوضح': 'clarifies',
        'يعلن': 'announces', 'يصدر': 'issues', 'يسري': 'is effective / applies',
        'يعمل': 'works / applies', 'تعمل': 'works / applies',
        'ابلغ': 'notified', 'أبلغ': 'notified', 'أُبلغ': 'was notified',
        'صادر': 'issued', 'الصادر': 'issued', 'صادرة': 'issued', 'الصادرة': 'issued',
        'مؤرخ': 'dated', 'المؤرخ': 'dated', 'مؤرخة': 'dated', 'المؤرخة': 'dated',
        'موقع': 'signed / located', 'الموقع': 'signed / located', 'موقعة': 'signed',
        'مسجل': 'registered', 'المسجل': 'registered', 'مسجلة': 'registered',
        'معتمد': 'approved', 'المعتمد': 'approved', 'معتمدة': 'approved',
        'محدد': 'specified', 'المحدد': 'specified', 'محددة': 'specified',
        'مطلوب': 'required', 'المطلوب': 'required', 'مطلوبة': 'required',
        'مرفق': 'attached', 'المرفق': 'attached',
        'موجه': 'addressed', 'الموجه': 'addressed', 'موجهة': 'addressed',
        'خاضع': 'subject to', 'الخاضع': 'subject to',
        'مختص': 'competent', 'المختص': 'competent', 'المختصة': 'competent',
        'أعلى': 'higher', 'أدنى': 'lower', 'أقصى': 'maximum', 'أدنى': 'minimum',
        'آخر': 'other / last', 'اخر': 'other / last', 'آخرين': 'others', 'اخرين': 'others',
        'أخرى': 'other', 'اخرى': 'other',
        'جديد': 'new', 'الجديد': 'new', 'جديدة': 'new', 'الجديدة': 'new',
        'قديم': 'old', 'القديم': 'old', 'قديمة': 'old', 'القديمة': 'old',
        'سابق': 'previous', 'السابق': 'previous', 'سابقة': 'previous', 'السابقة': 'previous',
        'لاحق': 'subsequent', 'اللاحق': 'subsequent', 'لاحقة': 'subsequent',
        'حالي': 'current', 'الحالي': 'current', 'حالية': 'current', 'الحالية': 'current',
        'مستقبل': 'future', 'المستقبل': 'future', 'مستقبلي': 'future',
        'رسمي': 'official', 'الرسمي': 'official', 'رسمية': 'official', 'الرسمية': 'official',
        'قانوني': 'legal', 'القانوني': 'legal', 'قانونية': 'legal', 'القانونية': 'legal',
        'إداري': 'administrative', 'اداري': 'administrative', 'الإداري': 'administrative',
        'مالي': 'financial', 'المالي': 'financial', 'مالية': 'financial', 'المالية': 'financial',
        'حكومي': 'governmental', 'الحكومي': 'governmental', 'حكومية': 'governmental',
        'عسكرية': 'military', 'العسكرية': 'military',
        'فني': 'technical', 'الفني': 'technical', 'فنية': 'technical',
        'صحيح': 'correct', 'الصحيح': 'correct', 'صحيحة': 'correct',
        'خطأ': 'error / wrong', 'الخطأ': 'error',
        'موثق': 'notarized / documented', 'الموثق': 'notarized',

        // Greetings & Closings
        'تحية': 'Greetings', 'التحية': 'Greetings', 'تقدير': 'Appreciation', 'التقدير': 'Appreciation',
        'احترام': 'Respect', 'الاحترام': 'Respect', 'شكر': 'Thanks', 'الشكر': 'Thanks',
        'تفضلوا': 'Please accept', 'فائق': 'highest', 'الفائق': 'highest',

        // Numbers in text
        'واحد': 'one', 'اثنان': 'two', 'ثلاثة': 'three', 'اربعة': 'four', 'أربعة': 'four',
        'خمسة': 'five', 'ستة': 'six', 'سبعة': 'seven', 'ثمانية': 'eight', 'تسعة': 'nine', 'عشرة': 'ten',
        'عشر': 'ten', 'عشرين': 'twenty', 'ثلاثين': 'thirty', 'اربعين': 'forty', 'أربعين': 'forty',
        'خمسين': 'fifty', 'ستين': 'sixty', 'سبعين': 'seventy', 'ثمانين': 'eighty', 'تسعين': 'ninety',
        'مائة': 'hundred', 'مئة': 'hundred', 'الف': 'thousand', 'ألف': 'thousand',
        'مليون': 'million',

        // Legal & Court
        'تخلف': 'default / failure', 'التخلف': 'default', 'امتناع': 'refusal', 'الامتناع': 'refusal',
        'إخلال': 'breach', 'اخلال': 'breach', 'الإخلال': 'breach',
        'إلغاء': 'cancellation', 'الغاء': 'cancellation', 'الإلغاء': 'cancellation',
        'سحب': 'withdrawal', 'السحب': 'withdrawal',
        'تنفيذ': 'enforcement', 'التنفيذ': 'enforcement',
        'دعوى': 'lawsuit', 'قضية': 'case', 'القضية': 'case', 'قضايا': 'cases',
        'حكم': 'ruling', 'الحكم': 'ruling', 'احكام': 'rulings', 'أحكام': 'rulings',
        'جلسة': 'hearing', 'الجلسة': 'hearing', 'جلسات': 'hearings',
        'إلزام': 'mandate', 'الزام': 'mandate',
        'مستحقات': 'outstanding dues', 'المستحقات': 'outstanding dues',
        'ديون': 'debts', 'الديون': 'debts', 'مديونية': 'indebtedness',
        'ذمة': 'liability', 'الذمة': 'liability',
        'تظلم': 'grievance', 'اعتراض': 'objection', 'الاعتراض': 'objection',
        'استئناف': 'appeal', 'الاستئناف': 'appeal',
        'إقرار': 'declaration', 'اقرار': 'declaration', 'الإقرار': 'declaration',

        // Housing Allocation & Construction
        'توزيع': 'distribution', 'التوزيع': 'distribution',
        'استحقاق': 'eligibility', 'الاستحقاق': 'eligibility',
        'معايير': 'criteria', 'المعايير': 'criteria',
        'أقدمية': 'seniority', 'اقدمية': 'seniority',
        'ترشيح': 'nomination', 'الترشيح': 'nomination',
        'تعديل': 'modification', 'التعديل': 'modification', 'تعديلات': 'modifications',
        'توسعة': 'extension', 'التوسعة': 'extension',
        'بناء': 'construction', 'البناء': 'construction',
        'هدم': 'demolition', 'الهدم': 'demolition',
        'إزالة': 'removal', 'ازالة': 'removal', 'الإزالة': 'removal',
        'معاينة': 'inspection', 'المعاينة': 'inspection',
        'فحص': 'examination', 'الفحص': 'examination',
        'عيب': 'defect', 'عيوب': 'defects', 'خلل': 'fault', 'الخلل': 'fault',
        'صالح': 'fit / valid', 'الصالح': 'fit',
        'جاهز': 'ready', 'جاهزة': 'ready', 'جاهزية': 'readiness',
        'مواصفات': 'specifications', 'المواصفات': 'specifications',
        'مخطط': 'layout / plan', 'المخطط': 'layout',
        'مساحة': 'area / size', 'المساحة': 'area',
        'متر': 'meter', 'أمتار': 'meters', 'امتار': 'meters', 'مربع': 'square',
        'حدود': 'boundaries', 'الحدود': 'boundaries',

        // Utilities & Maintenance
        'قطع': 'disconnection', 'القطع': 'disconnection',
        'إعادة': 'reconnection / restoration', 'اعادة': 'reconnection',
        'فصل': 'disconnection / separation', 'الفصل': 'disconnection',
        'توصيل': 'connection', 'التوصيل': 'connection',
        'تسريب': 'leakage', 'التسريب': 'leakage',
        'صرف': 'drainage / disbursement', 'الصرف': 'drainage',
        'خزان': 'tank', 'الخزان': 'tank',
        'تكييف': 'air conditioning', 'مكيف': 'AC unit',

        // Allowances & Payroll
        'علاوة': 'allowance', 'العلاوة': 'allowance',
        'مكافأة': 'bonus', 'المكافأة': 'bonus',
        'إيقاف': 'suspension', 'ايقاف': 'suspension', 'وقف': 'suspension / stopping',
        'تحويل': 'transfer', 'التحويل': 'transfer',
        'إيداع': 'deposit', 'ايداع': 'deposit',
        'خصم': 'deduction', 'الخصم': 'deduction',
        'دخل': 'income', 'الدخل': 'income',
        'معاش': 'pension', 'المعاش': 'pension',

        // Family & Personal
        'زوج': 'husband', 'الزوج': 'husband', 'زوجة': 'wife', 'الزوجة': 'wife',
        'ابن': 'son', 'الابن': 'son', 'ابناء': 'sons', 'أبناء': 'sons',
        'ابنة': 'daughter', 'الابنة': 'daughter', 'بنت': 'daughter',
        'اولاد': 'children', 'أولاد': 'children',
        'أسرة': 'family', 'اسرة': 'family', 'الأسرة': 'family',
        'عائلة': 'family', 'العائلة': 'family',
        'معيل': 'breadwinner', 'المعيل': 'breadwinner',
        'فرد': 'member', 'الفرد': 'member', 'افراد': 'members', 'أفراد': 'members',
        'أرملة': 'widow', 'ارملة': 'widow', 'مطلقة': 'divorcee',
        'ميلاد': 'birth', 'الميلاد': 'birth',
        'وفاة': 'death', 'الوفاة': 'death',
        'ورثة': 'heirs', 'الورثة': 'heirs',
        'داخلية': 'Interior', 'الداخلية': 'Interior',

        // Administrative & Eviction Terms
        'عدم': 'non- / lack of', 'لعدم': 'due to failure of / for non-',
        'تحديث': 'updating / renewal', 'لتحديث': 'to update',
        'مقر': 'headquarters / office / premises', 'المقر': 'headquarters',
        'شعبة': 'division / section', 'الشعبة': 'division',
        'قسم': 'department / section', 'القسم': 'department',
        'الشؤون': 'affairs', 'شؤون': 'affairs', 'الشئون': 'affairs', 'شئون': 'affairs',
        'أقصاها': 'maximum of', 'أقصى': 'maximum', 'اقصى': 'maximum', 'اقصاها': 'maximum of',
        'إجراءات': 'procedures / measures', 'الإجراءات': 'procedures / measures', 'اجراءات': 'procedures',
        'تسليم': 'handover / delivery', 'التسليم': 'handover', 'تسليمها': 'handing it over',
        'شواغل': 'occupants / encumbrances', 'الشواغل': 'occupants / encumbrances',
        'كافة': 'all', 'رسوم': 'fees', 'الرسوم': 'fees',
        'فواتير': 'bills / invoices', 'الفواتير': 'bills', 'فاتورة': 'bill / invoice', 'الفاتورة': 'bill',
        'ماء': 'water', 'الماء': 'water', 'مياه': 'water', 'المياه': 'water',
        'ختم': 'stamp / seal', 'الختم': 'stamp / seal',
        'تحريراً': 'issued / drawn up', 'تحرير': 'issuance / drafting',
        'تبدأ': 'starts / commences', 'تنتهي': 'ends / expires',
        'استلام': 'Receipt', 'الاستلام': 'Receipt',
        'أنظمة': 'systems / regulations', 'الأنظمة': 'systems / regulations',
        'لوائح': 'regulations / bylaws', 'اللوائح': 'regulations / bylaws',
        'مرفقات': 'attachments', 'المرفقات': 'attachments',
        'كشف': 'statement / disclosure', 'الكشف': 'statement',
        'أشهر': 'months', 'اشهر': 'months',
        'توقيع': 'signature', 'التوقيع': 'signature',
        'مؤجر': 'lessor / landlord', 'المؤجر': 'lessor / landlord',
        'مدة': 'duration / period', 'المدة': 'duration / period',
        'سنة': 'year', 'السنة': 'year',
        'قيمة': 'value / amount', 'القيمة': 'value / amount',
        'شهرية': 'monthly', 'الشهرية': 'monthly',
        'أجرة': 'rent / fee', 'الأجرة': 'rent / fee', 'اجرة': 'rent',
        'مستحق': 'due / payable', 'مستحقة': 'due / outstanding', 'المستحقة': 'due / outstanding',
        'ذكية': 'smart', 'الذكية': 'smart',
        'دولي': 'international', 'الدولي': 'international',
        'آيبان': 'IBAN', 'الآيبان': 'IBAN', 'ايبان': 'IBAN',
        'شارع': 'street / avenue', 'الشارع': 'street / avenue',
        'ديوان': 'bureau / court', 'الديوان': 'bureau',
        'وإلا': 'otherwise / or else', 'نظراً': 'given that / in view of', 'نظرا': 'given that',
        'التكرم': 'kindly', 'تكرم': 'kindness', 'حضور': 'attendance', 'الحضور': 'attendance',
        'التماس': 'petition / appeal', 'التماسات': 'petitions / appeals', 'الالتماس': 'petition',
        'إمداد': 'supply', 'الإمداد': 'supply', 'تموين': 'provisioning', 'التموين': 'provisioning',
        'سعادة': 'His Excellency', 'السعادة': 'Excellency',
        'نائب': 'Member of Parliament / Deputy', 'النائب': 'Member of Parliament', 'نواب': 'Deputies / MPs', 'النواب': 'Parliament / Deputies',
        'مجلس': 'Council / Board', 'المجلس': 'Council',
        'منسق': 'coordinator', 'تنسيق': 'coordination', 'التنسيق': 'coordination',
        'إحالة': 'referral', 'الإحالة': 'referral', 'محال': 'referred',
        'منتفع': 'beneficiary / tenant', 'المنتفع': 'beneficiary / tenant', 'مخالف': 'violator', 'المخالف': 'violator',
        'قضية': 'lawsuit / case', 'القضية': 'lawsuit / case', 'قضايا': 'cases',
        'إدارية': 'administrative', 'الإدارية': 'administrative',
        'استئناف': 'appeal', 'الاستئناف': 'appeal', 'مستأنف': 'appellant',
        'تنفيذ': 'enforcement', 'التنفيذ': 'enforcement',
        'تمديد': 'extension', 'التمديد': 'extension', 'مؤقت': 'temporary', 'المؤقت': 'temporary',
        'إنسانية': 'humanitarian', 'الإنسانية': 'humanitarian',
        'إشعار': 'Notice', 'الإشعار': 'Notice', 'إشعارات': 'Notices', 'الإشعارات': 'Notices'
    };

    // ── Bahraini & Arab Personal / Family Names ──
    const ARABIC_NAMES = {
        'محمد': 'Mohamed', 'علي': 'Ali', 'أحمد': 'Ahmed', 'احمد': 'Ahmed', 'حسن': 'Hassan',
        'حسين': 'Hussain', 'عبدالله': 'Abdullah', 'عبد الله': 'Abdullah', 'عبدالرحمن': 'Abdulrahman',
        'عبد الرحمن': 'Abdulrahman', 'عبدالعزيز': 'Abdulaziz', 'عبد العزيز': 'Abdulaziz',
        'خالد': 'Khalid', 'سلمان': 'Salman', 'عيسى': 'Isa', 'حمد': 'Hamad', 'ناصر': 'Nasser',
        'جاسم': 'Jassim', 'إبراهيم': 'Ibrahim', 'ابراهيم': 'Ibrahim', 'يوسف': 'Yousif',
        'خليفة': 'Khalifa', 'عمر': 'Omar', 'عثمان': 'Othman', 'راشد': 'Rashid', 'سعيد': 'Saeed',
        'فهد': 'Fahad', 'بدر': 'Bader', 'مبارك': 'Mubarak', 'ماجد': 'Majid', 'منصور': 'Mansoor',
        'طارق': 'Tariq', 'وليد': 'Waleed', 'فيصل': 'Faisal', 'جمال': 'Jamal', 'عادل': 'Adel',
        'نبيل': 'Nabeel', 'سامي': 'Sami', 'هشام': 'Hisham', 'فؤاد': 'Fouad', 'كمال': 'Kamal',
        'صلاح': 'Salah', 'مصطفى': 'Mustafa', 'سعود': 'Saud', 'غانم': 'Ghanem', 'صقر': 'Saqer',
        'جميل': 'Jameel', 'عمران': 'Omran', 'حبيب': 'Habib', 'يعقوب': 'Yaqoob', 'مهدي': 'Mahdi',
        'فاطمة': 'Fatima', 'مريم': 'Maryam', 'عائشة': 'Aisha', 'زينب': 'Zainab', 'سارة': 'Sarah',
        'نورة': 'Noora', 'منيرة': 'Muneera', 'هدى': 'Huda', 'لطيفة': 'Lateefa', 'أسماء': 'Asma',
        'اسماء': 'Asma', 'شيخة': 'Shaikha', 'دانة': 'Dana', 'ريم': 'Reem', 'ليلى': 'Layla',
        'خديجة': 'Khadija', 'أمينة': 'Amina', 'امينة': 'Amina',
        // Family Names & Prefixes
        'آل خليفة': 'Al Khalifa', 'الخليفة': 'Al Khalifa',
        'الدوسري': 'Al Doseri', 'دوسري': 'Al Doseri',
        'البوعينين': 'Al Buainain', 'بوعينين': 'Al Buainain',
        'النعيمي': 'Al Nuaimi', 'نعيمي': 'Al Nuaimi',
        'الكعبي': 'Al Kaabi', 'كعبي': 'Al Kaabi',
        'الجناحي': 'Janahi', 'جناحي': 'Janahi',
        'فخرو': 'Fakhro', 'كانو': 'Kanoo',
        'المؤيد': 'Almoayyed', 'مؤيد': 'Almoayyed',
        'المرخي': 'Al Markhi', 'مرخي': 'Al Markhi',
        'الحمادي': 'Al Hammadi', 'حمادي': 'Al Hammadi',
        'السادة': 'Al Sada', 'سادة': 'Al Sada',
        'الدرازي': 'Al Darazi', 'درازي': 'Al Darazi',
        'القاسم': 'Al Qasim', 'قاسم': 'Al Qasim',
        'الشروقي': 'Al Shorooqi', 'شروقي': 'Al Shorooqi',
        'السيار': 'Al Sayyar', 'سيار': 'Al Sayyar',
        'الزامل': 'Al Zamil', 'زامل': 'Al Zamil',
        'الغتم': 'Al Ghatam', 'غتم': 'Al Ghatam',
        'المطوع': 'Al Mutawa', 'مطوع': 'Al Mutawa',
        'الرومي': 'Al Roomi', 'رومي': 'Al Roomi',
        'الزايد': 'Al Zayed', 'زايد': 'Al Zayed',
        'العازمي': 'Al Azmi', 'عازمي': 'Al Azmi',
        'الهاجري': 'Al Hajeri', 'هاجري': 'Al Hajeri',
        'الرميحي': 'Al Romaihi', 'رميحي': 'Al Romaihi',
        'البنكي': 'Al Banki', 'بنكي': 'Al Banki',
        'الخاجة': 'Al Khaja', 'خاجة': 'Al Khaja',
        'حاجي': 'Haji', 'بهمن': 'Bahman', 'شمس': 'Shams',
        'بن': 'Bin', 'ابن': 'Ibn', 'آل': 'Al-', 'بو': 'Bu'
    };

    // ── Unicode Normalization & Dual Key Map ──
    function normalizeArabicText(text) {
        if (!text || typeof text !== 'string') return '';
        return text
            .normalize('NFKC')
            .replace(/[\u064B-\u065F\u0670\u0640]/g, '')
            .trim();
    }

    function normalizeArabicKey(str) {
        if (!str) return '';
        return normalizeArabicText(str)
            .replace(/[إأآٱ]/g, 'ا')
            .replace(/ة/g, 'ه')
            
            .replace(/[ؤئ]/g, 'ء');
    }

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function buildFlexiblePhraseRegex(phrase) {
        const clean = normalizeArabicText(phrase);
        let pat = '';
        for (let i = 0; i < clean.length; i++) {
            const ch = clean[i];
            if (ch === ' ') {
                pat += '\\s+';
            } else if (/[اإأآٱ]/.test(ch)) {
                pat += '[اإأآٱ]';
            } else if (/[ةه]/.test(ch)) {
                pat += '[ةه]';
            } else if (/[يى]/.test(ch)) {
                pat += '[يى]';
            } else if (/[ؤئء]/.test(ch)) {
                pat += '[ؤئء]';
            } else {
                pat += escapeRegex(ch);
            }
        }
        return new RegExp('(^|[^\\u0600-\\u06FFA-Za-z0-9])' + pat + '(?=[^\\u0600-\\u06FFA-Za-z0-9]|$)', 'gu');
    }

    // Pre-compile phrases (longest first)
    ARABIC_PHRASES.sort((a, b) => b.ar.length - a.ar.length);
    ARABIC_PHRASES.forEach(p => {
        p.regex = buildFlexiblePhraseRegex(p.ar);
    });

    const NORMALIZED_WORDS = new Map();
    for (const [k, v] of Object.entries(ARABIC_WORDS)) {
        NORMALIZED_WORDS.set(k, v);
        NORMALIZED_WORDS.set(normalizeArabicKey(k), v);
        if (k.endsWith('ة')) NORMALIZED_WORDS.set(k.slice(0, -1) + 'ه', v);
        if (k.endsWith('ه')) NORMALIZED_WORDS.set(k.slice(0, -1) + 'ة', v);
        if (k.startsWith('ا')) {
            NORMALIZED_WORDS.set('إ' + k.slice(1), v);
            NORMALIZED_WORDS.set('أ' + k.slice(1), v);
        }
    }

    const NORMALIZED_NAMES = new Map();
    for (const [k, v] of Object.entries(ARABIC_NAMES)) {
        NORMALIZED_NAMES.set(k, v);
        NORMALIZED_NAMES.set(normalizeArabicKey(k), v);
        if (k.endsWith('ة')) NORMALIZED_NAMES.set(k.slice(0, -1) + 'ه', v);
        if (k.endsWith('ه')) NORMALIZED_NAMES.set(k.slice(0, -1) + 'ة', v);
    }

    // ── Reverse Stream Detection & Un-reversing ──
    function detectAndUnreverseArabic(text) {
        if (!text || typeof text !== 'string') return text;
        const clean = normalizeArabicText(text);
        const words = clean.split(/\s+/).filter(Boolean);
        let reversedScore = 0;
        let normalScore = 0;
        for (const w of words) {
            // Strong reversed indicators:
            // ة at word start is impossible in valid Arabic typography
            if (w.startsWith('ة') && w.length > 1) reversedScore += 3;
            // لاو at word end (وال reversed) is impossible as a valid suffix
            if (w.endsWith('لاو') && w.length > 3) reversedScore += 3;
            // لاب at word end (بال reversed)
            if (w.endsWith('لاب') && w.length > 3) reversedScore += 3;
            // Unambiguous reversed vocabulary stems with zero legitimate Arabic collision
            // Note: 'مقر' is intentionally excluded because مقر is valid Arabic for Headquarters/Premises
            if (['دقع', 'راجيإ', 'ءابرهك', 'نكسم', 'ةرازو', 'ةرازاو', 'ةكلمم', 'خيرات', 'ينيرحب', 'عافد'].includes(w)) {
                reversedScore += 3;
            }

            // Normal Arabic stream indicators
            if (w.startsWith('ال') && w.length > 3) normalScore += 2;
            if (w.startsWith('وال') && w.length > 4) normalScore += 2;
            if (w.startsWith('بال') && w.length > 4) normalScore += 2;
            if (w.endsWith('ة') && w.length > 2) normalScore += 2;
            if (w.endsWith('ات') && w.length > 3) normalScore += 1;
        }
        // Only reverse if reversed indicators clearly dominate normal indicators
        if (reversedScore >= 3 && reversedScore > normalScore) {
            return clean.split('').reverse().join('');
        }
        return text;
    }

    function unreverseWordIfApplicable(word) {
        if (!word || word.length < 2) return word;
        const rev = word.split('').reverse().join('');
        if (word.startsWith('ة') || word.endsWith('لاو') || word.endsWith('لاب')) {
            return rev;
        }
        const knownReversedStems = ['دقع', 'راجيإ', 'ءابرهك', 'نكسم', 'ةرازو', 'ةرازاو', 'ةكلمم', 'خيرات', 'ينيرحب', 'عافد'];
        if (knownReversedStems.includes(word)) {
            return rev;
        }
        return word;
    }

    // ── Phonetic Transliteration Fallback (Used only for unknown proper/personal names) ──
    const ARABIC_CHAR_MAP = {
        'ا': 'a', 'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ء': '\'', 'ؤ': '\'', 'ئ': '\'',
        'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
        'ص': 's', 'ض': 'dh', 'ط': 't', 'ظ': 'dh', 'ع': 'a', 'غ': 'gh',
        'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
        'ه': 'h', 'ة': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a'
    };

    function transliterateArabic(word) {
        if (!word) return '';
        const clean = word.replace(/[\u064B-\u065F\u0670\u0640]/g, '');
        let res = '';
        for (let i = 0; i < clean.length; i++) {
            const ch = clean[i];
            if (ARABIC_CHAR_MAP[ch] !== undefined) {
                res += ARABIC_CHAR_MAP[ch];
            } else if (/[\u0600-\u06FF]/.test(ch)) {
                // Ignore unknown Arabic control chars
            } else {
                res += ch;
            }
        }
        if (!res) return word;
        return res.charAt(0).toUpperCase() + res.slice(1);
    }

    function lookupArabicStem(stem) {
        if (!stem) return null;
        if (NORMALIZED_WORDS.has(stem)) return NORMALIZED_WORDS.get(stem);
        if (ARABIC_NAMES[stem]) return ARABIC_NAMES[stem];

        const stemNorm = normalizeArabicKey(stem);
        if (NORMALIZED_WORDS.has(stemNorm)) return NORMALIZED_WORDS.get(stemNorm);
        if (NORMALIZED_NAMES.has(stemNorm)) return NORMALIZED_NAMES.get(stemNorm);

        if (stem.endsWith('ة') || stem.endsWith('ه')) {
            const alt = stem.endsWith('ة') ? (stem.slice(0, -1) + 'ه') : (stem.slice(0, -1) + 'ة');
            if (NORMALIZED_WORDS.has(alt)) return NORMALIZED_WORDS.get(alt);
            const altNorm = normalizeArabicKey(alt);
            if (NORMALIZED_WORDS.has(altNorm)) return NORMALIZED_WORDS.get(altNorm);
        }

        if (stem.endsWith('ت')) {
            const withTaa = stem.slice(0, -1) + 'ة';
            const withHaa = stem.slice(0, -1) + 'ه';
            if (NORMALIZED_WORDS.has(withTaa)) return NORMALIZED_WORDS.get(withTaa);
            if (NORMALIZED_WORDS.has(withHaa)) return NORMALIZED_WORDS.get(withHaa);
            const withTaaNorm = normalizeArabicKey(withTaa);
            if (NORMALIZED_WORDS.has(withTaaNorm)) return NORMALIZED_WORDS.get(withTaaNorm);
        }
        return null;
    }

    function translateArabicWord(rawWord) {
        if (!rawWord || typeof rawWord !== 'string') return '';
        let word = rawWord.trim();
        if (!word) return '';

        // Separate attached punctuation: e.g. "(المستأجر)" -> prefix "(", core "المستأجر", suffix ")"
        const m = word.match(/^([^\u0600-\u06FFA-Za-z0-9]*)([\u0600-\u06FF]+)([^\u0600-\u06FFA-Za-z0-9]*)$/);
        if (!m) {
            const direct = lookupArabicStem(word);
            return direct ? direct : transliterateArabic(word);
        }

        const prefixPunct = m[1] || '';
        let coreArabic = m[2];
        const suffixPunct = m[3] || '';

        // Un-reverse individual word if it exhibits reversal
        coreArabic = unreverseWordIfApplicable(coreArabic);

        // 1. Direct match
        const directCore = lookupArabicStem(coreArabic);
        if (directCore) {
            return prefixPunct + directCore + suffixPunct;
        }

        // 2. Morphological decomposition
        const prefixes = [
            { ar: 'وبال', en: 'and in the ' },
            { ar: 'ولل', en: 'and for the ' },
            { ar: 'وكال', en: 'and like the ' },
            { ar: 'فبال', en: 'so in the ' },
            { ar: 'فلل', en: 'so for the ' },
            { ar: 'وال', en: 'and the ' },
            { ar: 'فال', en: 'and the ' },
            { ar: 'بال', en: 'in the ' },
            { ar: 'لل', en: 'for the ' },
            { ar: 'كال', en: 'as the ' },
            { ar: 'ال', en: 'the ' },
            { ar: 'سي', en: 'will ' },
            { ar: 'س', en: 'will ' },
            { ar: 'وب', en: 'and with ' },
            { ar: 'ول', en: 'and to ' },
            { ar: 'و', en: 'and ' },
            { ar: 'ف', en: 'then ' },
            { ar: 'ب', en: 'in ' },
            { ar: 'ل', en: 'to ' }
        ];

        const suffixes = [
            { ar: 'هما', en: ' their' },
            { ar: 'هم', en: ' their' },
            { ar: 'هن', en: ' their' },
            { ar: 'كم', en: ' your' },
            { ar: 'نا', en: ' our' },
            { ar: 'ها', en: ' its' },
            { ar: 'ية', en: '' },
            { ar: 'يه', en: '' },
            { ar: 'ه', en: ' his' },
            { ar: 'ي', en: ' my' },
            { ar: 'ين', en: '' },
            { ar: 'ون', en: '' },
            { ar: 'ان', en: '' },
            { ar: 'ات', en: '' },
            { ar: 'ة', en: '' }
        ];

        // Try prefix only
        for (const p of prefixes) {
            if (coreArabic.startsWith(p.ar) && coreArabic.length > p.ar.length + 1) {
                const stem = coreArabic.slice(p.ar.length);
                const stemMatch = lookupArabicStem(stem);
                if (stemMatch) {
                    // When ال + name, use "Al" instead of "the"
                    if (p.ar === 'ال' && (ARABIC_NAMES[stem] || NORMALIZED_NAMES.has(stem) || NORMALIZED_NAMES.has(normalizeArabicKey(stem)))) {
                        return prefixPunct + 'Al ' + stemMatch + suffixPunct;
                    }
                    return prefixPunct + p.en + stemMatch + suffixPunct;
                }
            }
        }

        // Try suffix only
        for (const s of suffixes) {
            if (coreArabic.endsWith(s.ar) && coreArabic.length > s.ar.length + 1) {
                const stem = coreArabic.slice(0, -s.ar.length);
                const stemMatch = lookupArabicStem(stem);
                if (stemMatch) {
                    return prefixPunct + stemMatch + s.en + suffixPunct;
                }
            }
        }

        // Try prefix + suffix
        for (const p of prefixes) {
            if (coreArabic.startsWith(p.ar) && coreArabic.length > p.ar.length + 3) {
                const rem = coreArabic.slice(p.ar.length);
                for (const s of suffixes) {
                    if (rem.endsWith(s.ar) && rem.length > s.ar.length + 1) {
                        const stem = rem.slice(0, -s.ar.length);
                        const stemMatch = lookupArabicStem(stem);
                        if (stemMatch) {
                            return prefixPunct + p.en + stemMatch + s.en + suffixPunct;
                        }
                    }
                }
            }
        }

        // Fallback: Transliterate phonetically so no raw Arabic remains
        return prefixPunct + transliterateArabic(coreArabic) + suffixPunct;
    }

    function getEnglishCategory(category) {
        if (!category || typeof category !== 'string') {
            return { en: 'Official Housing Document', icon: '📄' };
        }
        const clean = category.trim();
        if (CATEGORY_TRANSLATIONS[clean]) {
            return CATEGORY_TRANSLATIONS[clean];
        }
        for (const [key, val] of Object.entries(CATEGORY_TRANSLATIONS)) {
            if (clean.includes(key.substring(5)) || key.includes(clean)) {
                return val;
            }
        }
        return { en: translateArabicText(clean) || 'Official Housing Document', icon: '📄' };
    }

    function translateArabicText(text) {
        if (!text || typeof text !== 'string') return '';
        let result = text.trim();
        if (!result) return '';

        // 0. Unicode normalization and strip diacritics / tatweel
        result = normalizeArabicText(result);

        // 1. Detect and un-reverse Arabic stream if visual RTL was reversed in PDF
        result = detectAndUnreverseArabic(result);

        // 2. Convert Eastern Arabic numerals to Western digits
        const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        arabicNumerals.forEach((ch, idx) => {
            result = result.replaceAll(ch, String(idx));
        });

        // 3. Normalize Arabic punctuation
        result = result
            .replaceAll('،', ', ')
            .replaceAll('؛', '; ')
            .replaceAll('؟', '? ');

        // 4. Multi-word phrase and entity replacements (longest first, boundary-aware)
        for (const item of ARABIC_PHRASES) {
            if (!item.regex) continue;
            item.regex.lastIndex = 0;
            result = result.replace(item.regex, (match, p1) => `${p1}${item.en}`);
        }

        // 5. Tokenize remaining words and translate individual Arabic words/names/stems
        if (/[\u0600-\u06FF]/.test(result)) {
            const tokens = result.split(/(\s+|[.,;:\-–—\(\)\[\]{}"'«»\u201C\u201D\u2018\u2019!?\u2026/\\•]+)/);
            result = tokens.map(tok => {
                if (!tok || !/[\u0600-\u06FF]/.test(tok)) {
                    return tok;
                }
                return translateArabicWord(tok);
            }).join('');
        }

        return result.replace(/\s+/g, ' ').trim();
    }

    function escapeHtml(str) {
        if (!str || typeof str !== 'string') return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatContentParagraphs(text) {
        if (!text || typeof text !== 'string') return '<p class="italic text-slate-400">No content explanation available for this page.</p>';
        const clean = text.trim();
        if (!clean) return '<p class="italic text-slate-400">No content explanation available for this page.</p>';

        const paragraphs = clean.split(/\n\s*\n|\r\n\s*\r\n/);
        return paragraphs.map(p => {
            const pTrim = p.trim();
            if (!pTrim) return '';
            return `<p class="leading-relaxed mb-2 last:mb-0">${escapeHtml(pTrim)}</p>`;
        }).filter(Boolean).join('');
    }

    const docMetadataCache = new Map();

    async function fetchDocumentMetadata(vaultId) {
        if (!vaultId) return null;
        if (docMetadataCache.has(vaultId)) {
            return docMetadataCache.get(vaultId);
        }

        const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || 'default';
        const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || 'default';

        let meta = null;
        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/metadata`);
            if (res.ok) {
                meta = await res.json();
            }
        } catch (e) {}

        if (!meta) {
            try {
                const altRes = await fetch(`/api/documents/${encodeURIComponent(vaultId)}/metadata`);
                if (altRes.ok) {
                    meta = await altRes.json();
                }
            } catch (e) {}
        }

        if (meta) {
            docMetadataCache.set(vaultId, meta);
        }
        return meta;
    }

    let isTranslationActive = false;
    try {
        isTranslationActive = (typeof localStorage !== 'undefined') ? (localStorage.getItem('doc_viewer_translate') === 'true') : false;
    } catch (e) {}

    function updateTranslationButtonState() {
        const btn = document.getElementById('viewer-translate-btn');
        const label = document.getElementById('viewer-translate-label');
        if (!btn) return;

        if (isTranslationActive) {
            btn.classList.remove('bg-blue-950/40', 'text-blue-300', 'border-blue-600/50', 'hover:bg-blue-800/60');
            btn.classList.add('bg-blue-600', 'text-white', 'border-blue-500', 'shadow-xs', 'ring-2', 'ring-blue-400/40');
            btn.setAttribute('aria-pressed', 'true');
            btn.title = 'Translation active (English overlay enabled) — Click to view original scan • الترجمة مفعلة — انقر لإظهار المسح الأصلي';
            if (label) label.textContent = 'English (Active)';
        } else {
            btn.classList.add('bg-blue-950/40', 'text-blue-300', 'border-blue-600/50', 'hover:bg-blue-800/60');
            btn.classList.remove('bg-blue-600', 'text-white', 'border-blue-500', 'shadow-xs', 'ring-2', 'ring-blue-400/40');
            btn.setAttribute('aria-pressed', 'false');
            btn.title = 'Translate document to English (Offline) • ترجمة المستند للإنجليزية';
            if (label) label.textContent = 'English';
        }
    }

    const pageOcrCache = new Map();
    let tesseractWorker = null;
    let tesseractLoadingPromise = null;

    async function getTesseractWorker() {
        if (tesseractWorker) return tesseractWorker;
        if (tesseractLoadingPromise) return tesseractLoadingPromise;

        tesseractLoadingPromise = (async () => {
            if (typeof Tesseract === 'undefined') {
                console.warn('Tesseract.js is not loaded.');
                return null;
            }
            try {
                let basePath = '/lib/tesseract';
                if (typeof window !== 'undefined' && window.location) {
                    if (window.location.origin && window.location.origin !== 'null' && !window.location.origin.startsWith('file')) {
                        basePath = window.location.origin + '/lib/tesseract';
                    } else {
                        basePath = 'lib/tesseract';
                    }
                }

                const createPromise = Tesseract.createWorker('ara', 1, {
                    workerPath: `${basePath}/worker.min.js`,
                    corePath: `${basePath}/tesseract-core-simd-lstm.wasm.js`,
                    langPath: basePath,
                    gzip: true
                });
                const timeoutPromise = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Tesseract worker init timed out after 10s')), 10000)
                );
                const worker = await Promise.race([createPromise, timeoutPromise]);
                tesseractWorker = worker;
                return worker;
            } catch (err) {
                console.error('Failed to initialize local Tesseract worker:', err);
                return null;
            } finally {
                tesseractLoadingPromise = null;
            }
        })();
        return tesseractLoadingPromise;
    }

    function clusterPdfItemsIntoLines(items, viewportHeight) {
        if (!items || items.length === 0) return [];
        const valid = [];
        for (let idx = 0; idx < items.length; idx++) {
            const it = items[idx];
            if (!it.str || !it.str.trim()) continue;
            const tx = it.transform || [1, 0, 0, 1, 0, 0];
            const h = it.height || 14;
            const w = it.width || (it.str.length * (h * 0.55));
            const x0 = tx[4];
            const y0 = Math.max(0, viewportHeight - tx[5] - h);
            const x1 = x0 + w;
            const y1 = y0 + h;
            valid.push({
                idx,
                str: it.str.normalize('NFKC'),
                x0, y0, x1, y1, h, w
            });
        }
        if (valid.length === 0) return [];

        // Group into line clusters based on vertical proximity without scrambling intra-line word order
        const clusters = [];
        for (const item of valid) {
            const cluster = clusters.find(c => Math.abs(c.y0 - item.y0) <= Math.max(6, item.h * 0.55));
            if (cluster) {
                cluster.items.push(item);
                cluster.x0 = Math.min(cluster.x0, item.x0);
                cluster.y0 = Math.min(cluster.y0, item.y0);
                cluster.x1 = Math.max(cluster.x1, item.x1);
                cluster.y1 = Math.max(cluster.y1, item.y1);
            } else {
                clusters.push({
                    y0: item.y0,
                    x0: item.x0,
                    x1: item.x1,
                    y1: item.y1,
                    items: [item]
                });
            }
        }

        // Sort lines top-to-bottom
        clusters.sort((a, b) => a.y0 - b.y0);

        const lines = [];
        for (const cluster of clusters) {
            // Within each line cluster, maintain original stream index (reading order)
            cluster.items.sort((a, b) => a.idx - b.idx);
            let lineText = cluster.items.map(it => it.str).join(' ').replace(/\s+/g, ' ').trim();
            if (lineText.length > 0) {
                lineText = detectAndUnreverseArabic(lineText);
                lines.push({
                    text: lineText,
                    bbox: {
                        x0: cluster.x0,
                        y0: cluster.y0,
                        x1: cluster.x1,
                        y1: cluster.y1
                    }
                });
            }
        }
        return lines;
    }

    async function detectPageText(pageWrapper, pageNum, vaultId, pdfDoc) {
        const cacheKey = `${vaultId}_p${pageNum}`;
        if (pageOcrCache.has(cacheKey)) {
            return pageOcrCache.get(cacheKey);
        }

        const canvas = pageWrapper ? pageWrapper.querySelector('canvas.pdf-page-canvas') : null;

        // 1. Primary: Database Metadata (Instant & accurate AI/DB translation)
        try {
            const meta = await fetchDocumentMetadata(vaultId);
            if (meta) {
                if (meta.pages && Array.isArray(meta.pages) && meta.pages.length > 0) {
                    const p = meta.pages.find(x => (x.page_number || x.pageNumber) === pageNum)
                           || meta.pages[pageNum - 1]
                           || (pageNum === 1 ? meta.pages[0] : null);
                    if (p) {
                        const lines = [];
                        if (p.subject) {
                            const subTr = translateArabicText(p.subject);
                            lines.push({
                                text: subTr ? `Subject: ${subTr}` : p.subject,
                                original: p.subject
                            });
                        }
                        if (p.sender) {
                            const sndTr = translateArabicText(p.sender);
                            lines.push({
                                text: sndTr ? `From: ${sndTr}` : p.sender,
                                original: p.sender
                            });
                        }
                        if (p.receiver) {
                            const rcvTr = translateArabicText(p.receiver);
                            lines.push({
                                text: rcvTr ? `To: ${rcvTr}` : p.receiver,
                                original: p.receiver
                            });
                        }
                        if (p.content_explanation) {
                            const hasAr = /[\u0600-\u06FF]/.test(p.content_explanation);
                            const explTr = hasAr ? translateArabicText(p.content_explanation) : p.content_explanation;
                            lines.push({
                                text: explTr,
                                original: p.content_explanation
                            });
                        }
                        if (lines.length > 0) {
                            pageOcrCache.set(cacheKey, lines);
                            return lines;
                        }
                    }
                } else if (meta.arabic_title || meta.category || meta.notes) {
                    const lines = [];
                    if (meta.arabic_title) {
                        const tTr = translateArabicText(meta.arabic_title);
                        lines.push({ text: `Document: ${tTr}`, original: meta.arabic_title });
                    }
                    if (meta.category) {
                        const catObj = getEnglishCategory(meta.category);
                        lines.push({ text: `Category: ${catObj.en || meta.category}`, original: meta.category });
                    }
                    if (meta.notes) {
                        lines.push({ text: `Notes: ${translateArabicText(meta.notes)}`, original: meta.notes });
                    }
                    if (lines.length > 0) {
                        pageOcrCache.set(cacheKey, lines);
                        return lines;
                    }
                }
            }
        } catch (e) {
            console.debug('Metadata extraction fallback to PDF/OCR:', e);
        }

        // 2. Secondary: Digital text layer from PDF.js if available
        if (pdfDoc) {
            try {
                const page = await pdfDoc.getPage(pageNum);
                const viewport = page.getViewport({ scale: 1.0 });
                const textContent = await page.getTextContent();
                if (textContent && textContent.items && textContent.items.length > 0) {
                    const arabicItems = textContent.items.filter(it => it.str && /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFC]/.test(it.str));
                    if (arabicItems.length > 0) {
                        const lines = clusterPdfItemsIntoLines(textContent.items, viewport.height);
                        if (lines.length > 0) {
                            pageOcrCache.set(cacheKey, lines);
                            return lines;
                        }
                    }
                }
            } catch (e) {
                console.debug('PDF text layer extraction fallback to OCR:', e);
            }
        }

        // 3. Fallback: Client-side Offline OCR via Local Tesseract.js
        if (canvas && typeof Tesseract !== 'undefined') {
            const indicator = pageWrapper ? pageWrapper.querySelector('.ocr-scanning-indicator') : null;
            try {
                const worker = await getTesseractWorker();
                if (worker) {
                    // Downscale canvas to max 1200px width for fast, reliable offline OCR
                    let ocrCanvas = canvas;
                    if (canvas.width > 1200) {
                        const scale = 1200 / canvas.width;
                        const scaled = document.createElement('canvas');
                        scaled.width = 1200;
                        scaled.height = Math.round(canvas.height * scale);
                        const sCtx = scaled.getContext('2d');
                        if (sCtx) {
                            sCtx.drawImage(canvas, 0, 0, scaled.width, scaled.height);
                            ocrCanvas = scaled;
                        }
                    }

                    const ocrPromise = worker.recognize(ocrCanvas);
                    const timeoutPromise = new Promise((_, reject) =>
                        setTimeout(() => reject(new Error('OCR recognition timed out after 12 seconds')), 12000)
                    );
                    const res = await Promise.race([ocrPromise, timeoutPromise]);

                    if (res && res.data) {
                        let lines = [];
                        if (res.data.lines && res.data.lines.length > 0) {
                            lines = res.data.lines
                                .filter(l => l.text && l.text.trim().length > 0)
                                .map(l => ({
                                    text: l.text.trim(),
                                    bbox: l.bbox,
                                    words: l.words
                                }));
                        } else if (res.data.text && res.data.text.trim().length > 0) {
                            lines = res.data.text
                                .split('\n')
                                .map(t => t.trim())
                                .filter(t => t.length > 0)
                                .map(text => ({ text }));
                        }
                        if (lines.length > 0) {
                            pageOcrCache.set(cacheKey, lines);
                            return lines;
                        }
                    }
                }
            } catch (err) {
                console.error('Tesseract offline OCR error:', err);
            }
        }

        return [];
    }

    async function renderPageTranslationLayer(pageWrapper, pageNum, vaultId) {
        if (!pageWrapper) return;
        const canvas = pageWrapper.querySelector('canvas.pdf-page-canvas');
        if (!canvas) return;

        // Remove any existing translation panel for this page
        let panel = pageWrapper.parentElement
            ? pageWrapper.parentElement.querySelector(`.pdf-translation-panel[data-page-number="${pageNum}"]`)
            : null;
        if (panel) panel.remove();
        const oldLayer = pageWrapper.querySelector(`.pdf-translation-layer[data-page-number="${pageNum}"]`);
        if (oldLayer) oldLayer.remove();

        // Show a per-page translation progress badge while analyzing
        const indicator = document.createElement('div');
        indicator.className = 'ocr-scanning-indicator';
        indicator.style.cssText = 'position:absolute;top:8px;left:8px;padding:4px 12px;border-radius:12px;background:rgba(15,23,42,0.85);color:white;font-size:11px;z-index:30;pointer-events:none;display:flex;align-items:center;gap:6px;backdrop-filter:blur(4px);';
        indicator.innerHTML = `
            <svg style="width:14px;height:14px;animation:spin 1s linear infinite;flex-shrink:0;" fill="none" viewBox="0 0 24 24"><circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
            <span>Translating page ${pageNum}...</span>
        `;
        pageWrapper.appendChild(indicator);

        try {
            console.debug(`[Translation] Page ${pageNum}: detecting text...`);
            const lines = await detectPageText(pageWrapper, pageNum, vaultId, currentPdfDoc);

            indicator.remove();

            if (!lines || lines.length === 0) {
                console.debug(`[Translation] Page ${pageNum}: no text detected`);
                const noticePanel = document.createElement('div');
                noticePanel.className = 'pdf-translation-panel';
                noticePanel.setAttribute('data-page-number', pageNum);
                noticePanel.style.cssText = 'width:100%;max-width:816px;margin:0 auto 16px auto;background:rgba(15,23,42,0.85);border:1px solid rgba(148,163,184,0.2);border-radius:12px;padding:14px 20px;text-align:center;color:#94a3b8;font-size:13px;backdrop-filter:blur(6px);';
                noticePanel.innerHTML = `<span style="color:#e2e8f0;font-weight:600;">Page ${pageNum}</span>: No extractable text or metadata found for this page.`;
                if (pageWrapper.nextSibling) {
                    pageWrapper.parentElement.insertBefore(noticePanel, pageWrapper.nextSibling);
                } else {
                    pageWrapper.parentElement.appendChild(noticePanel);
                }
                return;
            }

            // Collect and translate all text lines
            const translatedLines = [];
            lines.forEach(line => {
                if (!line || !line.text) return;
                const origText = line.text.trim();
                if (!origText || origText.length < 1) return;

                const hasArabic = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFC]/.test(origText);
                const translated = hasArabic ? translateArabicText(origText) : origText;
                if (translated && translated.trim()) {
                    translatedLines.push({
                        original: line.original || origText,
                        translated: translated.trim()
                    });
                }
            });

            if (translatedLines.length === 0) return;

            // Build the translation panel — inserted AFTER the page wrapper inside the canvas container
            panel = document.createElement('div');
            panel.className = 'pdf-translation-panel';
            panel.setAttribute('data-page-number', pageNum);

            // Page header
            const header = document.createElement('div');
            header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-bottom:1px solid rgba(148,163,184,0.25);';
            header.innerHTML = `
                <div style="display:flex;align-items:center;gap:8px;">
                    <svg style="width:16px;height:16px;color:#3b82f6;flex-shrink:0;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/></svg>
                    <span style="font-size:13px;font-weight:600;color:#e2e8f0;">Page ${pageNum} — English Translation & Summary</span>
                </div>
                <span style="font-size:11px;color:#64748b;">${translatedLines.length} item${translatedLines.length === 1 ? '' : 's'}</span>
            `;
            panel.appendChild(header);

            // Translation content
            const content = document.createElement('div');
            content.style.cssText = 'padding:14px 18px;display:flex;flex-direction:column;gap:8px;';

            translatedLines.forEach(item => {
                const lineEl = document.createElement('div');
                lineEl.style.cssText = 'font-size:14px;line-height:1.6;color:#f1f5f9;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:3px 0;';
                lineEl.textContent = item.translated;
                if (item.original && item.original !== item.translated) {
                    lineEl.setAttribute('title', `Original: ${item.original}`);
                    lineEl.style.cursor = 'help';
                }
                content.appendChild(lineEl);
            });

            panel.appendChild(content);

            // Style the panel
            panel.style.cssText = [
                'width:100%',
                'max-width:816px',
                'margin:0 auto 16px auto',
                'background:linear-gradient(135deg,rgba(15,23,42,0.95),rgba(30,41,59,0.95))',
                'border:1px solid rgba(148,163,184,0.2)',
                'border-radius:12px',
                'backdrop-filter:blur(8px)',
                'box-shadow:0 4px 16px rgba(0,0,0,0.2)',
                'overflow:hidden',
                'user-select:text',
            ].join(';') + ';';

            // Insert AFTER the page wrapper in the canvas container
            if (pageWrapper.nextSibling) {
                pageWrapper.parentElement.insertBefore(panel, pageWrapper.nextSibling);
            } else {
                pageWrapper.parentElement.appendChild(panel);
            }
        } catch (err) {
            console.error(`[Translation] Page ${pageNum}: error during translation:`, err);
            indicator.remove();
            const errorPanel = document.createElement('div');
            errorPanel.className = 'pdf-translation-panel';
            errorPanel.setAttribute('data-page-number', pageNum);
            errorPanel.style.cssText = 'width:100%;max-width:816px;margin:0 auto 16px auto;background:rgba(127,29,29,0.3);border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:12px 16px;text-align:center;color:#fca5a5;font-size:12px;';
            errorPanel.textContent = `Page ${pageNum}: Translation failed — ${err.message || 'Unknown error'}`;
            if (pageWrapper.nextSibling) {
                pageWrapper.parentElement.insertBefore(errorPanel, pageWrapper.nextSibling);
            } else {
                pageWrapper.parentElement.appendChild(errorPanel);
            }
        }
    }

    // ── Overlay-based Translation for Tablet/Touch Devices ──────────────────
    // Shows translation cards on top of the iframe PDF viewer.
    // No canvas rendering needed — fast, lightweight, touch-friendly.
    async function renderOverlayTranslation(vaultId) {
        const overlay = document.getElementById('document-translation-overlay');
        if (!overlay) return;

        // Show overlay on top of iframe — iframe stays visible underneath
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');

        // Show loading spinner while fetching metadata
        overlay.innerHTML = `
            <div class="flex flex-col items-center justify-center p-8 bg-white/95 dark:bg-slate-900/95 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 gap-3 my-auto max-w-sm text-center">
                <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <div class="text-sm font-semibold text-slate-800 dark:text-slate-100">Translating Document</div>
                <div class="text-xs text-slate-500 dark:text-slate-400">Loading translation from database...</div>
            </div>
        `;

        try {
            const meta = await fetchDocumentMetadata(vaultId);

            // Bail out if document changed or translation was deactivated while loading
            if (!currentPinnedDoc || currentPinnedDoc.vaultId !== vaultId || !isTranslationActive) {
                return;
            }

            overlay.innerHTML = '';

            const pages = (meta && Array.isArray(meta.pages) && meta.pages.length > 0) ? meta.pages : null;

            if (!pages) {
                // Fallback card when no per-page metadata is available
                const docTitle = currentPinnedDoc.title || 'Official Document';
                const catInfo = getEnglishCategory(currentPinnedDoc.category || (meta && meta.category));
                const tenant = currentPinnedDoc.tenant_name || currentPinnedDoc.tenant || (meta && meta.tenant_name) || '';
                const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || (meta && meta.house_id) || '';
                const date = (meta && meta.primary_date) || '';

                const fallbackCard = document.createElement('div');
                fallbackCard.className = 'translation-page-sheet relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200/90 dark:border-slate-800 p-6 sm:p-8 space-y-4 text-slate-800 dark:text-slate-100 my-auto select-text';
                fallbackCard.innerHTML = `
                    <div class="flex items-center justify-between gap-2 pb-3 border-b border-slate-200/80 dark:border-slate-800">
                        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                            <span>${catInfo.icon}</span>
                            <span>${escapeHtml(catInfo.en)}</span>
                        </span>
                        <button type="button" class="btn-peek-scan text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 transition-all cursor-pointer select-none">
                            <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                            <span>View Scan</span>
                        </button>
                    </div>
                    <div class="p-3 bg-blue-50/50 dark:bg-blue-950/20 rounded-xl border border-blue-100 dark:border-blue-900/40">
                        <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block mb-0.5">Document Title:</span>
                        <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(docTitle)}</div>
                    </div>
                    <div class="text-xs text-slate-600 dark:text-slate-400 space-y-1.5">
                        ${house ? `<div><strong>House:</strong> ${escapeHtml(String(house))}</div>` : ''}
                        ${tenant ? `<div><strong>Tenant:</strong> ${escapeHtml(tenant)}</div>` : ''}
                        ${date ? `<div><strong>Date:</strong> ${escapeHtml(date)}</div>` : ''}
                    </div>
                    <div class="text-slate-700 dark:text-slate-300 text-sm leading-relaxed border-t border-slate-100 dark:border-slate-800 pt-3">
                        <p>This is an official document stored in the housing archive under category <strong>${escapeHtml(catInfo.en)}</strong>. Tap <strong>View Scan</strong> to see the original document underneath.</p>
                    </div>
                `;
                attachOverlayPeekBehavior(fallbackCard, overlay);
                overlay.appendChild(fallbackCard);
                return;
            }

            // Render per-page translation cards
            const totalPages = pages.length;
            pages.forEach((p, idx) => {
                const pageNum = p.page_number || p.pageNumber || idx + 1;
                const catInfo = getEnglishCategory(p.fine_category || p.fineCategory || (meta && meta.category) || (currentPinnedDoc && currentPinnedDoc.category));
                const dateText = p.raw_date || p.rawDate || (meta && meta.primary_date) || '';

                const origContent = p.content_explanation || p.contentExplanation || '';
                const origSubject = p.subject || '';
                const origSender = p.sender || '';
                const origReceiver = p.receiver || '';

                // content_explanation is already English from AI — display directly
                let contentText = '';
                if (origContent) {
                    const hasEnglish = /[a-zA-Z]/.test(origContent);
                    contentText = hasEnglish ? origContent : translateArabicText(origContent);
                } else {
                    contentText = `Official archive record (${catInfo.en}). Associated with house ${(meta && meta.house_id) || ''}${(meta && meta.tenant_name) ? ', tenant ' + meta.tenant_name : ''}.`;
                }

                // subject/sender/receiver are Arabic — translate them
                const subjectText = origSubject ? (/[a-zA-Z]/.test(origSubject) ? origSubject : translateArabicText(origSubject)) : '';
                const senderText = origSender ? (/[a-zA-Z]/.test(origSender) ? origSender : translateArabicText(origSender)) : '';
                const receiverText = origReceiver ? (/[a-zA-Z]/.test(origReceiver) ? origReceiver : translateArabicText(origReceiver)) : '';

                const pageCard = document.createElement('div');
                pageCard.className = 'translation-page-sheet relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200/90 dark:border-slate-800 p-5 sm:p-7 space-y-4 text-slate-800 dark:text-slate-100 select-text transition-all';
                pageCard.setAttribute('data-page-number', pageNum);

                pageCard.innerHTML = `
                    <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200/80 dark:border-slate-800">
                        <div class="flex items-center gap-2">
                            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                                <span>${catInfo.icon}</span>
                                <span>${escapeHtml(catInfo.en)}</span>
                            </span>
                            <span class="text-xs font-mono text-slate-400 dark:text-slate-500">Page ${pageNum} of ${totalPages}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            ${dateText ? `<span class="text-xs text-slate-500 dark:text-slate-400 font-mono">${escapeHtml(dateText)}</span>` : ''}
                            <button type="button" class="btn-peek-scan text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 transition-all cursor-pointer select-none">
                                <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                                <span>View Scan</span>
                            </button>
                        </div>
                    </div>

                    ${(senderText || receiverText) ? `
                    <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">
                        ${senderText ? `
                        <div class="flex items-start gap-1.5 min-w-0">
                            <span class="font-bold text-slate-500 uppercase text-[10px] tracking-wider flex-shrink-0 mt-0.5">FROM:</span>
                            <span class="text-slate-700 dark:text-slate-200 font-medium">${escapeHtml(senderText)}</span>
                        </div>` : ''}
                        ${receiverText ? `
                        <div class="flex items-start gap-1.5 min-w-0">
                            <span class="font-bold text-slate-500 uppercase text-[10px] tracking-wider flex-shrink-0 mt-0.5">TO:</span>
                            <span class="text-slate-700 dark:text-slate-200 font-medium">${escapeHtml(receiverText)}</span>
                        </div>` : ''}
                    </div>` : ''}

                    ${subjectText ? `
                    <div class="p-3 bg-blue-50/50 dark:bg-blue-950/20 rounded-xl border border-blue-100 dark:border-blue-900/40">
                        <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block mb-0.5">Subject / Title:</span>
                        <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(subjectText)}</div>
                    </div>` : ''}

                    <div class="space-y-2">
                        <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">Document Content & Translation:</span>
                        <div class="text-slate-700 dark:text-slate-200 text-sm sm:text-[15px] leading-relaxed space-y-2 font-normal">
                            ${formatContentParagraphs(contentText)}
                        </div>
                    </div>

                    ${(origSubject || origSender || origReceiver || origContent) ? `
                    <details class="group mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                        <summary class="cursor-pointer text-xs font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 flex items-center justify-between select-none">
                            <span class="flex items-center gap-1.5">
                                <svg class="w-3.5 h-3.5 text-slate-400 group-open:rotate-90 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                                <span>Original Arabic</span>
                            </span>
                            <span class="text-[10px] font-mono text-slate-400">النص الأصلي</span>
                        </summary>
                        <div class="mt-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/60 dark:border-slate-800 font-arabic text-xs text-slate-600 dark:text-slate-400 space-y-2" dir="rtl">
                            ${origSubject ? `<div><strong class="text-slate-700 dark:text-slate-300">الموضوع:</strong> ${escapeHtml(origSubject)}</div>` : ''}
                            ${(origSender || origReceiver) ? `
                            <div class="flex flex-wrap gap-x-4 gap-y-1">
                                ${origSender ? `<div><strong class="text-slate-700 dark:text-slate-300">من:</strong> ${escapeHtml(origSender)}</div>` : ''}
                                ${origReceiver ? `<div><strong class="text-slate-700 dark:text-slate-300">إلى:</strong> ${escapeHtml(origReceiver)}</div>` : ''}
                            </div>` : ''}
                            ${origContent ? `<div class="leading-relaxed border-t border-slate-200/40 dark:border-slate-800 pt-1.5 mt-1.5">${escapeHtml(origContent)}</div>` : ''}
                        </div>
                    </details>` : ''}
                `;

                attachOverlayPeekBehavior(pageCard, overlay);
                overlay.appendChild(pageCard);
            });
        } catch (err) {
            console.error('[Translation] Overlay translation failed:', err);
            overlay.innerHTML = `
                <div class="flex flex-col items-center justify-center p-8 bg-white/95 dark:bg-slate-900/95 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 gap-3 my-auto max-w-sm text-center">
                    <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 flex items-center justify-center mb-1">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                    </div>
                    <div class="text-sm font-semibold text-red-600 dark:text-red-400">Translation Error</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">${escapeHtml(err.message || 'Could not load translation')}</div>
                </div>
            `;
        }
    }

    function attachOverlayPeekBehavior(card, overlay) {
        if (!card || !overlay) return;
        card.querySelectorAll('.btn-peek-scan').forEach(btn => {
            let timeout = null;
            const startPeek = () => { card.classList.add('peeking'); };
            const stopPeek = () => {
                card.classList.remove('peeking');
                if (timeout) { clearTimeout(timeout); timeout = null; }
            };

            btn.addEventListener('pointerdown', startPeek);
            btn.addEventListener('pointerup', stopPeek);
            btn.addEventListener('pointerleave', stopPeek);
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                if (card.classList.contains('peeking')) {
                    stopPeek();
                } else {
                    startPeek();
                    timeout = setTimeout(stopPeek, 4000);
                }
            });
        });
    }

    let currentTranslationPromise = null;

    async function renderDocumentTranslation() {
        if (!currentPinnedDoc || !currentPinnedDoc.vaultId) {
            console.debug('[Translation] No pinned document, skipping translation');
            return;
        }
        const vaultId = currentPinnedDoc.vaultId;
        const pdfUrl = resolvePdfUrl(vaultId);

        if (currentTranslationPromise) {
            console.debug('[Translation] Translation already in progress, reusing promise');
            return currentTranslationPromise;
        }

        console.debug('[Translation] Starting document translation for:', vaultId);

        // Desktop / Tab: use canvas-based translation panels below each rendered page
        currentTranslationPromise = (async () => {
            try {
                const canvasContainer = document.getElementById('pdf-canvas-container');
                const pdfFrame = document.getElementById('pdf-frame');
                const overlay = document.getElementById('document-translation-overlay');

                if (pdfFrame) pdfFrame.classList.add('hidden');
                if (canvasContainer) canvasContainer.classList.remove('hidden');
                if (overlay) {
                    overlay.classList.add('hidden');
                    overlay.classList.remove('flex');
                    overlay.innerHTML = '';
                }

                const wrappers = canvasContainer ? canvasContainer.querySelectorAll('.pdf-page-wrapper') : [];
                console.debug(`[Translation] Existing page wrappers: ${wrappers.length}, currentPdfDoc: ${!!currentPdfDoc}, pdfUrl match: ${currentPdfUrl === pdfUrl}`);
                if (!currentPdfDoc || currentPdfUrl !== pdfUrl || wrappers.length === 0) {
                    console.debug('[Translation] Rendering PDF document first...');
                    await renderPdfDocument(pdfUrl);
                    console.debug('[Translation] PDF document rendered');
                } else {
                    const freshWrappers = canvasContainer ? canvasContainer.querySelectorAll('.pdf-page-wrapper') : [];
                    console.debug(`[Translation] Processing ${freshWrappers.length} existing pages for translation`);
                    for (let i = 0; i < freshWrappers.length; i++) {
                        const pageWrapper = freshWrappers[i];
                        const pageNum = parseInt(pageWrapper.getAttribute('data-page-number') || String(i + 1), 10);
                        await renderPageTranslationLayer(pageWrapper, pageNum, vaultId);
                    }
                }
                console.debug('[Translation] All pages processed');
            } catch (err) {
                console.error('[Translation] Document translation failed:', err);
            }
        })().finally(() => {
            currentTranslationPromise = null;
        });

        return currentTranslationPromise;
    }

    function removeDocumentTranslation() {
        const canvasContainer = document.getElementById('pdf-canvas-container');
        if (canvasContainer) {
            canvasContainer.querySelectorAll('.pdf-translation-layer').forEach(l => l.remove());
            canvasContainer.querySelectorAll('.pdf-translation-panel').forEach(l => l.remove());
            canvasContainer.querySelectorAll('.ocr-scanning-indicator').forEach(i => i.remove());
            canvasContainer.classList.add('hidden');
        }
        const overlay = document.getElementById('document-translation-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
            overlay.classList.remove('flex');
            overlay.innerHTML = '';
        }

        const pdfFrame = document.getElementById('pdf-frame');
        if (pdfFrame && currentPinnedDoc && currentPinnedDoc.vaultId) {
            pdfFrame.classList.remove('hidden');
            const pdfUrl = resolvePdfUrl(currentPinnedDoc.vaultId);
            loadPdfIntoFrame(pdfFrame, pdfUrl);
        }
    }

    function toggleDocumentTranslation() {
        isTranslationActive = !isTranslationActive;
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('doc_viewer_translate', isTranslationActive ? 'true' : 'false');
            }
        } catch (e) {}

        updateTranslationButtonState();

        if (isTranslationActive) {
            renderDocumentTranslation();
        } else {
            removeDocumentTranslation();
        }
    }


    function isVaultHashName(name) {
        if (!name || typeof name !== 'string') return false;
        const clean = name.trim();
        // Matches patterns like doc_ac132cf0...pdf, ac132cf0...pdf, or hex hash >= 16 chars
        return /^(?:doc_)?[0-9a-f]{16,}(?:\.pdf)?$/i.test(clean);
    }

    function getCleanDocTitle(doc, fallbackCategory = null) {
        if (!doc) return fallbackCategory || 'وثيقة';
        if (typeof doc === 'string') {
            return isVaultHashName(doc) ? (fallbackCategory || 'وثيقة') : doc.trim();
        }
        const arabicTitle = doc.brief_arabic_title || doc.arabic_title;
        if (arabicTitle && !isVaultHashName(arabicTitle)) {
            return arabicTitle.trim();
        }
        const title = doc.title;
        if (title && !isVaultHashName(title)) {
            return title.trim();
        }
        const filename = doc.filename || doc.file_name || doc.name;
        if (filename && !isVaultHashName(filename)) {
            return filename.trim();
        }
        const category = doc.category || doc.folder || doc.subfolder || fallbackCategory;
        if (category && typeof category === 'string' && category.trim()) {
            return category.trim();
        }
        return 'وثيقة';
    }

    function resolvePdfUrl(vaultId) {
        if (typeof getPdfUrl === 'function' && typeof currentArea !== 'undefined' && typeof currentHouse !== 'undefined') {
            return getPdfUrl(currentArea, currentHouse, vaultId);
        }
        return `/api/areas/default/houses/default/pdf/${encodeURIComponent(vaultId)}`;
    }

    function shouldUseOfficialViewer() {
        let stored = null;
        try {
            stored = (typeof localStorage !== 'undefined') ? localStorage.getItem('pdf_viewer_mode') : null;
        } catch (e) {}

        if (stored === 'tab' || stored === 'tablet' || stored === 'pdfjs' || stored === 'official' || stored === 'canvas') return true;
        if (stored === 'computer' || stored === 'native') return false;

        // In automated test runners (Playwright/Puppeteer), prefer native iframe for desktop assertions unless explicitly set
        if (typeof navigator !== 'undefined' && navigator.webdriver) {
            return false;
        }

        // On tab (tablet/mobile), default mode should be tab (official PDF.js viewer)
        // On computer (desktop/laptop), default mode should be computer (native PDF viewer)
        if (typeof navigator !== 'undefined') {
            const ua = navigator.userAgent || '';
            const isMobileOrTabletUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet/i.test(ua);
            const isIPad = /Macintosh/i.test(ua) && navigator.maxTouchPoints > 1;

            if (isMobileOrTabletUA || isIPad) return true;

            // Fallback for devices without native PDF viewer plugin (tablets/mobile)
            if (navigator.pdfViewerEnabled === false) return true;
        }

        // Default for computer: native iframe (ensures desktop plugins & PDF viewers work)
        return false;
    }

    function shouldUseCanvasViewer() {
        return shouldUseOfficialViewer();
    }

    function getPreferredPdfZoom() {
        try {
            if (typeof localStorage !== 'undefined') {
                const stored = localStorage.getItem('pdf_zoom_preference');
                if (stored) return stored;
            }
        } catch (e) {}
        return shouldUseOfficialViewer() ? 'page-fit' : 'page-width';
    }

    function setPreferredPdfZoom(zoomValue) {
        if (!zoomValue) return;
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('pdf_zoom_preference', zoomValue);
            }
        } catch (e) {}
    }

    function resolveViewerSrc(pdfUrl) {
        const preferredZoom = getPreferredPdfZoom();
        if (shouldUseOfficialViewer()) {
            const hash = preferredZoom ? `#zoom=${encodeURIComponent(preferredZoom)}` : '#zoom=page-fit';
            return `/lib/pdfjs/web/viewer.html?file=${encodeURIComponent(pdfUrl)}${hash}`;
        }
        if (preferredZoom === 'page-fit' || preferredZoom === 'Fit') {
            return pdfUrl + '#view=Fit';
        }
        if (preferredZoom === 'page-width' || preferredZoom === 'FitH') {
            return pdfUrl + '#view=FitH';
        }
        const num = parseFloat(preferredZoom);
        if (!isNaN(num) && num > 0) {
            const pct = num <= 5 ? Math.round(num * 100) : Math.round(num);
            return `${pdfUrl}#zoom=${pct}`;
        }
        return pdfUrl + '#view=FitH';
    }

    function loadPdfIntoFrame(pdfFrame, pdfUrl) {
        if (!pdfFrame) return;
        const targetSrc = resolveViewerSrc(pdfUrl);
        const preferredZoom = getPreferredPdfZoom();

        let reusedViewer = false;
        if (shouldUseOfficialViewer()) {
            try {
                const frameWin = pdfFrame.contentWindow;
                if (frameWin && frameWin.PDFViewerApplication && frameWin.PDFViewerApplication.initialized && typeof frameWin.PDFViewerApplication.open === 'function') {
                    const app = frameWin.PDFViewerApplication;

                    try {
                        if (frameWin._app_options && frameWin._app_options.AppOptions) {
                            frameWin._app_options.AppOptions.set('defaultZoomValue', preferredZoom);
                        }
                    } catch (e) {}

                    const applyCurrentZoom = () => {
                        try {
                            const curZoom = getPreferredPdfZoom();
                            if (curZoom && app.pdfViewer) {
                                if (app.pdfViewer.currentScaleValue === curZoom) {
                                    return;
                                }
                                const container = app.pdfViewer.container;
                                const prevScrollTop = container ? container.scrollTop : 0;
                                if (typeof app.pdfViewer.setScale === 'function') {
                                    app.pdfViewer.setScale(curZoom, { noScroll: prevScrollTop > 0 });
                                } else {
                                    app.pdfViewer.currentScaleValue = curZoom;
                                }
                                if (container && prevScrollTop > 0) {
                                    container.scrollTop = prevScrollTop;
                                }
                                app.toolbar?.setPageScale(curZoom, app.pdfViewer.currentScale);
                            }
                        } catch (err) {}
                    };

                    if (app.eventBus && !pdfFrame._hasScaleListener) {
                        pdfFrame._hasScaleListener = true;
                        app.eventBus._on('scalechanged', function(evt) {
                            if (evt && evt.value) {
                                setPreferredPdfZoom(evt.value);
                            }
                        });
                        app.eventBus._on('scalechanging', function(evt) {
                            if (evt && evt.presetValue) {
                                setPreferredPdfZoom(evt.presetValue);
                            }
                        });
                    }

                    if (app.eventBus && !pdfFrame._hasDocInitListeners) {
                        pdfFrame._hasDocInitListeners = true;
                        const onPagesReady = () => {
                            applyCurrentZoom();
                        };
                        app.eventBus._on('pagesloaded', onPagesReady);
                        app.eventBus._on('documentinit', onPagesReady);
                    }

                    const openPromise = app.open({ url: pdfUrl });
                    if (openPromise && typeof openPromise.then === 'function') {
                        openPromise.then(() => {
                            applyCurrentZoom();
                        }).catch(() => {});
                    }

                    reusedViewer = true;
                }
            } catch (e) {
                reusedViewer = false;
            }
        }

        if (!reusedViewer && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }

        if (!pdfFrame._hasLoadZoomListener && typeof pdfFrame.addEventListener === 'function') {
            pdfFrame._hasLoadZoomListener = true;
            pdfFrame.addEventListener('load', function() {
                try {
                    const win = pdfFrame.contentWindow;
                    if (win && win.PDFViewerApplication && win.PDFViewerApplication.eventBus) {
                        const app = win.PDFViewerApplication;
                        if (!pdfFrame._hasScaleListener) {
                            pdfFrame._hasScaleListener = true;
                            app.eventBus._on('scalechanged', function(evt) {
                                if (evt && evt.value) {
                                    setPreferredPdfZoom(evt.value);
                                }
                            });
                            app.eventBus._on('scalechanging', function(evt) {
                                if (evt && evt.presetValue) {
                                    setPreferredPdfZoom(evt.presetValue);
                                }
                            });
                        }
                        const applyZoom = () => {
                            const curZoom = getPreferredPdfZoom();
                            if (curZoom && app.pdfViewer) {
                                if (app.pdfViewer.currentScaleValue === curZoom) {
                                    return;
                                }
                                const container = app.pdfViewer.container;
                                const prevScrollTop = container ? container.scrollTop : 0;
                                if (typeof app.pdfViewer.setScale === 'function') {
                                    app.pdfViewer.setScale(curZoom, { noScroll: prevScrollTop > 0 });
                                } else {
                                    app.pdfViewer.currentScaleValue = curZoom;
                                }
                                if (container && prevScrollTop > 0) {
                                    container.scrollTop = prevScrollTop;
                                }
                                app.toolbar?.setPageScale(curZoom, app.pdfViewer.currentScale);
                            }
                        };
                        if (!pdfFrame._hasDocInitListeners) {
                            pdfFrame._hasDocInitListeners = true;
                            app.eventBus._on('pagesloaded', applyZoom);
                            app.eventBus._on('documentinit', applyZoom);
                        }
                    }
                } catch (err) {}
            });
        }

        pdfFrame.classList.remove('hidden');
    }

    function updateViewerCategory(vaultId, explicitCategory) {
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');
        if (!catBadge || !catVal) return;

        let foundCategory = explicitCategory || null;

        // If doc object was passed as category
        if (foundCategory && typeof foundCategory === 'object') {
            foundCategory = foundCategory.category || foundCategory.folder || foundCategory.subfolder || null;
        }

        // 1. Try finding in currentTimeline
        if (!foundCategory && typeof currentTimeline !== 'undefined' && Array.isArray(currentTimeline)) {
            const item = currentTimeline.find(d => d && (d.vault_id === vaultId || d.id === vaultId));
            if (item && item.category) {
                foundCategory = item.category;
            }
        }

        // 2. Try finding in window.getSelectedDoc()
        if (!foundCategory && typeof window.getSelectedDoc === 'function') {
            const sel = window.getSelectedDoc();
            if (sel && (sel.vaultId === vaultId || sel.doc?.vault_id === vaultId) && sel.doc?.category) {
                foundCategory = sel.doc.category;
            }
        }

        // 3. Try finding in globalTreeData
        if (!foundCategory) {
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
            const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse);
            if (tree && area && house) {
                const areaNode = tree.find(a => a.name === area);
                const houseNode = areaNode?.houses?.find(h => String(h.house_number || h.name) === String(house));
                if (houseNode && houseNode.categories) {
                    for (const cat of houseNode.categories) {
                        if (cat.documents && cat.documents.some(d => (d.vault_id === vaultId || d.id === vaultId))) {
                            foundCategory = cat.name;
                            break;
                        }
                    }
                }
            }
        }

        if (foundCategory) {
            catVal.textContent = foundCategory;
            catBadge.classList.remove('hidden');
            catBadge.classList.add('flex');
        } else {
            catVal.textContent = '';
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');

            // Asynchronous fetch from metadata API if not static mode
            if (typeof isStaticMode === 'undefined' || !isStaticMode) {
                const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || 'default';
                const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || 'default';
                fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/metadata`)
                    .then(res => res.ok ? res.json() : null)
                    .then(meta => {
                        if (meta && meta.category && catBadge && catVal && (!currentPinnedDoc || currentPinnedDoc.vaultId === vaultId)) {
                            catVal.textContent = meta.category;
                            catBadge.classList.remove('hidden');
                            catBadge.classList.add('flex');
                        }
                    })
                    .catch(() => {});
            }
        }
    }

    async function renderPdfDocument(pdfUrl) {
        const canvasContainer = document.getElementById('pdf-canvas-container');
        const pdfLoading = document.getElementById('pdf-viewer-loading');
        const pdfError = document.getElementById('pdf-viewer-error');
        const pageInfo = document.getElementById('viewer-page-info');
        const zoomControls = document.getElementById('viewer-zoom-controls');
        const pdfFrame = document.getElementById('pdf-frame');

        if (typeof pdfjsLib === 'undefined') {
            // Fallback to iframe if pdfjsLib is unavailable
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            return;
        }

        // Setup PDF.js worker path
        if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
            try {
                pdfjsLib.GlobalWorkerOptions.workerSrc = (typeof window !== 'undefined' && window.location ? window.location.origin : '') + '/lib/pdfjs/pdf.worker.min.js';
            } catch (e) {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdfjs/pdf.worker.min.js';
            }
        }

        if (pdfFrame) pdfFrame.classList.add('hidden');
        if (canvasContainer) {
            canvasContainer.classList.remove('hidden');
            canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());
        }
        if (pdfLoading) pdfLoading.classList.remove('hidden');
        if (pdfError) pdfError.classList.add('hidden');

        if (currentLoadingTask) {
            try { currentLoadingTask.destroy(); } catch (e) {}
            currentLoadingTask = null;
        }

        try {
            currentLoadingTask = pdfjsLib.getDocument(pdfUrl);
            // Add timeout to prevent infinite "loading document" state
            const timeoutMs = 15000;
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('PDF loading timed out after 15 seconds')), timeoutMs)
            );
            const pdf = await Promise.race([currentLoadingTask.promise, timeoutPromise]);
            currentPdfDoc = pdf;
            currentPdfUrl = pdfUrl;

            // Hide loading overlay immediately once PDF is fetched —
            // renderPdfPages (which includes OCR) can take 30-60s per page
            // and must NOT block behind the loading spinner.
            if (pdfLoading) pdfLoading.classList.add('hidden');

            if (pageInfo) {
                pageInfo.textContent = `${pdf.numPages} ${pdf.numPages === 1 ? 'صفحة' : 'صفحات'}`;
                pageInfo.classList.remove('hidden');
            }
            if (zoomControls) {
                zoomControls.classList.remove('hidden');
                zoomControls.classList.add('flex');
            }

            await renderPdfPages();
        } catch (err) {
            console.error('Failed to load PDF with PDF.js:', err);
            if (pdfLoading) pdfLoading.classList.add('hidden');
            if (pdfError) {
                pdfError.classList.remove('hidden');
                const errMsg = document.getElementById('pdf-viewer-error-msg');
                if (errMsg) errMsg.textContent = err.message || 'Error loading PDF';
                const fallbackLink = document.getElementById('pdf-viewer-fallback-link');
                if (fallbackLink) fallbackLink.href = pdfUrl;
            }
            // If PDF.js fails to render, show iframe fallback
            if (pdfFrame) pdfFrame.classList.remove('hidden');
        }
    }

    async function renderPdfPages() {
        if (!currentPdfDoc) return;
        const canvasContainer = document.getElementById('pdf-canvas-container');
        if (!canvasContainer) return;

        // Clear existing rendered pages
        canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());

        const zoomLevelBtn = document.getElementById('viewer-zoom-level');
        if (zoomLevelBtn) {
            zoomLevelBtn.textContent = currentScaleMode === 'fit' ? 'Fit' : `${Math.round(currentScale * 100)}%`;
        }

        const containerWidth = Math.max((canvasContainer.clientWidth || window.innerWidth * 0.5) - 32, 280);
        const outputScale = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;

        const activePdfDoc = currentPdfDoc;
        for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
            if (!currentPdfDoc || currentPdfDoc !== activePdfDoc) break;

            const page = await currentPdfDoc.getPage(pageNum);
            const unscaledViewport = page.getViewport({ scale: 1.0 });

            let scale = currentScale;
            if (currentScaleMode === 'fit') {
                scale = Math.min(Math.max(containerWidth / unscaledViewport.width, 0.4), 2.5);
            }

            const viewport = page.getViewport({ scale });

            const pageWrapper = document.createElement('div');
            pageWrapper.className = 'pdf-page-wrapper relative bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200 dark:border-slate-700 flex flex-col items-center my-3 overflow-hidden flex-shrink-0';
            pageWrapper.style.flexShrink = '0';
            pageWrapper.style.width = Math.floor(viewport.width) + 'px';
            pageWrapper.style.minHeight = Math.floor(viewport.height) + 'px';
            pageWrapper.style.height = Math.floor(viewport.height) + 'px';
            pageWrapper.setAttribute('data-page-number', pageNum);

            const pageBadge = document.createElement('div');
            pageBadge.className = 'absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900/70 text-white backdrop-blur-xs z-10 pointer-events-none shadow-xs';
            pageBadge.textContent = `${pageNum} / ${currentPdfDoc.numPages}`;
            pageWrapper.appendChild(pageBadge);

            const canvas = document.createElement('canvas');
            canvas.className = 'pdf-page-canvas block mx-auto flex-shrink-0';
            canvas.width = Math.floor(viewport.width * outputScale);
            canvas.height = Math.floor(viewport.height * outputScale);
            canvas.style.width = Math.floor(viewport.width) + 'px';
            canvas.style.height = Math.floor(viewport.height) + 'px';
            canvas.style.minHeight = Math.floor(viewport.height) + 'px';
            canvas.style.flexShrink = '0';

            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.scale(outputScale, outputScale);
            }

            pageWrapper.appendChild(canvas);
            canvasContainer.appendChild(pageWrapper);

            if (ctx) {
                await page.render({
                    canvasContext: ctx,
                    viewport: viewport
                }).promise;
            }

            if (isTranslationActive && currentPinnedDoc && currentPinnedDoc.vaultId) {
                await renderPageTranslationLayer(pageWrapper, pageNum, currentPinnedDoc.vaultId);
            }
        }
    }

    function toggleFullscreen() {
        const panel = document.getElementById('document-viewer-panel');
        if (!panel) return;
        const isFullscreen = panel.classList.toggle('fullscreen-viewer');
        const expandIcon = document.getElementById('viewer-expand-icon');
        const collapseIcon = document.getElementById('viewer-collapse-icon');
        const expandBtn = document.getElementById('viewer-expand-btn');
        if (expandIcon && collapseIcon) {
            if (isFullscreen) {
                expandIcon.classList.add('hidden');
                collapseIcon.classList.remove('hidden');
                if (expandBtn) expandBtn.title = 'Exit fullscreen • تصغير الشاشة';
            } else {
                expandIcon.classList.remove('hidden');
                collapseIcon.classList.add('hidden');
                if (expandBtn) expandBtn.title = 'Toggle fullscreen • شاشة كاملة';
            }
        }
    }

    function initViewerControls() {
        const closeBtn = document.getElementById('viewer-close-btn');
        if (closeBtn) {
            closeBtn.onclick = (e) => {
                e.preventDefault();
                closeDocument();
            };
        }

        const expandBtn = document.getElementById('viewer-expand-btn');
        if (expandBtn) {
            expandBtn.onclick = (e) => {
                e.preventDefault();
                toggleFullscreen();
            };
        }

        const editPagesBtn = document.getElementById('viewer-edit-pages-btn');
        if (editPagesBtn) {
            editPagesBtn.onclick = (e) => {
                e.preventDefault();
                if (currentPinnedDoc && typeof window.openPageEditor === 'function') {
                    const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
                    const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse);
                    window.openPageEditor({
                        vault_id: currentPinnedDoc.vaultId,
                        title: currentPinnedDoc.title,
                        category: currentPinnedDoc.category,
                        area_id: area,
                        house_id: house,
                        tenant: currentPinnedDoc.tenant || currentPinnedDoc.tenant_name || '',
                        tenant_name: currentPinnedDoc.tenant_name || currentPinnedDoc.tenant || '',
                        tenant_id: currentPinnedDoc.tenant_id || null
                    }, currentPinnedDoc.category);
                }
            };
        }

        const modeToggleBtn = document.getElementById('viewer-mode-toggle');
        if (modeToggleBtn) {
            modeToggleBtn.onclick = (e) => {
                e.preventDefault();
                const currentIsTab = shouldUseOfficialViewer();
                const newMode = currentIsTab ? 'computer' : 'tab';
                try {
                    localStorage.setItem('pdf_viewer_mode', newMode);
                } catch (err) {}
                updateViewerModeButton(newMode);

                if (isTranslationActive) {
                    isTranslationActive = false;
                    try {
                        localStorage.setItem('doc_viewer_translate', 'false');
                    } catch (err) {}
                    updateTranslationButtonState();
                    removeDocumentTranslation();
                }

                if (currentPinnedDoc && currentPinnedDoc.vaultId) {
                    const pdfUrl = resolvePdfUrl(currentPinnedDoc.vaultId);
                    const pdfFrame = document.getElementById('pdf-frame');
                    const canvasContainer = document.getElementById('pdf-canvas-container');
                    if (canvasContainer) canvasContainer.classList.add('hidden');
                    if (pdfFrame) {
                        loadPdfIntoFrame(pdfFrame, pdfUrl);
                    }
                }
            };
        }

        const translateBtn = document.getElementById('viewer-translate-btn');
        if (translateBtn) {
            translateBtn.onclick = (e) => {
                e.preventDefault();
                toggleDocumentTranslation();
            };
        }
        updateTranslationButtonState();

        const initialMode = shouldUseOfficialViewer() ? 'tab' : 'computer';
        updateViewerModeButton(initialMode);
    }

    function updateViewerModeButton(mode) {
        const label = document.getElementById('viewer-mode-label');
        const iconSvg = document.getElementById('viewer-mode-icon');
        const toggleBtn = document.getElementById('viewer-mode-toggle');
        if (!toggleBtn) return;
        const isTab = mode === 'tab' || mode === 'tablet' || mode === 'pdfjs' || mode === 'official' || mode === 'canvas' || (mode === null && shouldUseOfficialViewer());
        if (label) {
            label.textContent = isTab ? 'Tab' : 'Computer';
        }
        if (iconSvg) {
            if (isTab) {
                iconSvg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>';
            } else {
                iconSvg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>';
            }
        }
        toggleBtn.title = isTab 
            ? 'Using Tab viewer — Click to switch to Computer viewer • وضع التابلت — انقر للتبديل إلى وضع الكمبيوتر' 
            : 'Using Computer viewer — Click to switch to Tab viewer • وضع الكمبيوتر — انقر للتبديل إلى وضع التابلت';
    }

    let lastOpenDocVaultId = null;
    let lastOpenDocTime = 0;

    function openDocument(vaultId, title, category = null) {
        initViewerControls();

        const now = Date.now();
        if (lastOpenDocVaultId === vaultId && (now - lastOpenDocTime < 350) && currentPinnedDoc && currentPinnedDoc.vaultId === vaultId) {
            return;
        }
        lastOpenDocVaultId = vaultId;
        lastOpenDocTime = now;

        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const resizer2 = document.getElementById('resizer-2');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerPeekBadge = document.getElementById('viewer-peek-badge');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (documentEmptyState) {
            documentEmptyState.classList.add('hidden');
            documentEmptyState.classList.remove('flex');
        }
        if (resizer2) resizer2.classList.remove('hidden');

        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');

        const cleanTitle = getCleanDocTitle(title, category);
        if (viewerTitle) viewerTitle.textContent = cleanTitle;
        let tenantName = '';
        let tenantId = null;
        if (typeof currentTimeline !== 'undefined' && Array.isArray(currentTimeline)) {
            const item = currentTimeline.find(d => d && (d.vault_id === vaultId || d.id === vaultId));
            if (item) {
                tenantName = item.tenant || item.tenant_name || item.primary_tenant || '';
                tenantId = item.tenant_id || item.tenantId || null;
            }
        }
        if (!tenantName && typeof window.getSelectedDoc === 'function') {
            const sel = window.getSelectedDoc();
            if (sel && (sel.vaultId === vaultId || sel.doc?.vault_id === vaultId)) {
                tenantName = sel.doc?.tenant || sel.doc?.tenant_name || '';
                tenantId = sel.doc?.tenant_id || null;
            }
        }

        currentPinnedDoc = {
            vaultId,
            title: cleanTitle,
            category,
            tenant: tenantName,
            tenant_name: tenantName,
            tenant_id: tenantId
        };

        const pdfUrl = resolvePdfUrl(vaultId);
        loadPdfIntoFrame(pdfFrame, pdfUrl);
        if (viewerDownload) {
            viewerDownload.href = pdfUrl;
            viewerDownload.setAttribute('download', `${cleanTitle}.pdf`);
        }

        updateViewerCategory(vaultId, category);

        if (isTranslationActive) {
            renderDocumentTranslation();
        } else {
            const canvasContainer = document.getElementById('pdf-canvas-container');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            const overlay = document.getElementById('document-translation-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.classList.remove('flex');
            }
        }
    }

    function peekDocument(vaultId, title, category = null) {
        initViewerControls();

        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const resizer2 = document.getElementById('resizer-2');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerPeekBadge = document.getElementById('viewer-peek-badge');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (documentEmptyState) {
            documentEmptyState.classList.add('hidden');
            documentEmptyState.classList.remove('flex');
        }
        if (resizer2) resizer2.classList.remove('hidden');

        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');

        const cleanTitle = getCleanDocTitle(title, category);
        if (viewerTitle) viewerTitle.textContent = cleanTitle;
        if (viewerPeekBadge) viewerPeekBadge.classList.remove('hidden');

        currentPinnedDoc = {
            vaultId,
            title: cleanTitle,
            category,
            tenant: '',
            tenant_name: '',
            tenant_id: null
        };

        const pdfUrl = resolvePdfUrl(vaultId);
        loadPdfIntoFrame(pdfFrame, pdfUrl);
        if (viewerDownload) {
            viewerDownload.href = pdfUrl;
            viewerDownload.setAttribute('download', `${cleanTitle}.pdf`);
        }

        updateViewerCategory(vaultId, category);

        if (isTranslationActive) {
            renderDocumentTranslation();
        } else {
            const canvasContainer = document.getElementById('pdf-canvas-container');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            const overlay = document.getElementById('document-translation-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.classList.remove('flex');
            }
        }
    }

    function closeDocument() {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const pdfFrame = document.getElementById('pdf-frame');
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');
        const overlay = document.getElementById('document-translation-overlay');

        currentPinnedDoc = null;
        if (currentPdfDoc) {
            try { currentPdfDoc.destroy(); } catch (e) {}
            currentPdfDoc = null;
        }
        currentPdfUrl = null;
        if (currentLoadingTask) {
            try { currentLoadingTask.destroy(); } catch (e) {}
            currentLoadingTask = null;
        }

        removeDocumentTranslation();

        if (pdfFrame) pdfFrame.src = 'about:blank';

        const canvasContainer = document.getElementById('pdf-canvas-container');
        if (canvasContainer) {
            canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());
            canvasContainer.classList.add('hidden');
        }

        if (docViewerPanel) {
            docViewerPanel.classList.remove('fullscreen-viewer');
            docViewerPanel.classList.add('hidden');
            docViewerPanel.classList.remove('flex');
            const expandIcon = document.getElementById('viewer-expand-icon');
            const collapseIcon = document.getElementById('viewer-collapse-icon');
            if (expandIcon) expandIcon.classList.remove('hidden');
            if (collapseIcon) collapseIcon.classList.add('hidden');
        }

        const activeHouse = (typeof currentHouse !== 'undefined' && currentHouse) || (typeof window !== 'undefined' && window.currentHouse);
        if (activeHouse) {
            if (welcomePanel) welcomePanel.classList.add('hidden');
            if (documentEmptyState) {
                documentEmptyState.classList.remove('hidden');
                documentEmptyState.classList.add('flex');
            }
        } else {
            if (welcomePanel) welcomePanel.classList.remove('hidden');
            if (documentEmptyState) {
                documentEmptyState.classList.add('hidden');
                documentEmptyState.classList.remove('flex');
            }
        }
        if (catBadge) {
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');
        }
        if (catVal) catVal.textContent = '';
    }

    function reloadCurrentDocument(forceCacheBust = false) {
        if (!currentPinnedDoc || !currentPinnedDoc.vaultId) return;
        const vaultId = currentPinnedDoc.vaultId;
        const pdfFrame = document.getElementById('pdf-frame');
        let pdfUrl = resolvePdfUrl(vaultId);
        if (forceCacheBust) {
            const sep = pdfUrl.includes('?') ? '&' : '?';
            pdfUrl = `${pdfUrl}${sep}t=${Date.now()}`;
        }
        loadPdfIntoFrame(pdfFrame, pdfUrl);
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initViewerControls);
        } else {
            initViewerControls();
        }
    }

    window.openDocument = openDocument;
    window.peekDocument = peekDocument;
    window.closeDocument = closeDocument;
    window.reloadCurrentDocument = reloadCurrentDocument;
    window.getPinnedDoc = () => currentPinnedDoc;
    window.updateViewerCategory = updateViewerCategory;
    window.getCleanDocTitle = getCleanDocTitle;
    window.isVaultHashName = isVaultHashName;
    window.renderPdfDocument = renderPdfDocument;
    window.shouldUseCanvasViewer = shouldUseOfficialViewer;
    window.shouldUseOfficialViewer = shouldUseOfficialViewer;
    window.shouldUseTabViewer = shouldUseOfficialViewer;
    window.updateViewerModeButton = updateViewerModeButton;
    window.resolveViewerSrc = resolveViewerSrc;
    window.getPreferredPdfZoom = getPreferredPdfZoom;
    window.setPreferredPdfZoom = setPreferredPdfZoom;
    window.resolvePdfUrl = resolvePdfUrl;
    window.toggleFullscreen = toggleFullscreen;
    window.initViewerControls = initViewerControls;
    window.toggleDocumentTranslation = toggleDocumentTranslation;
    window.renderDocumentTranslation = renderDocumentTranslation;
    window.removeDocumentTranslation = removeDocumentTranslation;
    window.renderPageTranslationLayer = renderPageTranslationLayer;
    window.detectPageText = detectPageText;
    window.isDocumentTranslationActive = () => isTranslationActive;
    window.translateArabicText = translateArabicText;
    window.translateArabicWord = translateArabicWord;
    window.detectAndUnreverseArabic = detectAndUnreverseArabic;
    window.unreverseWordIfApplicable = unreverseWordIfApplicable;
    window.lookupArabicStem = lookupArabicStem;
    window.transliterateArabic = transliterateArabic;
    window.clusterPdfItemsIntoLines = clusterPdfItemsIntoLines;
    window.getEnglishCategory = getEnglishCategory;
    window.updateTranslationButtonState = updateTranslationButtonState;
})();
