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
        { ar: 'هيئة الكهرباء والماء', en: 'Electricity & Water Authority (EWA)' },
        { ar: 'فرع إسكان الشرطة', en: 'Police Housing Branch' },
        { ar: 'فرع القضايا العامة', en: 'General Cases Branch' },
        { ar: 'رئاسة الأمن العام', en: 'Public Security Headquarters' },
        { ar: 'قوة دفاع البحرين', en: 'Bahrain Defence Force' },
        { ar: 'الحرس الوطني', en: 'National Guard' },
        { ar: 'جهاز الأمن الوطني', en: 'National Security Agency' },
        { ar: 'الديوان الملكي', en: 'Royal Court' },
        { ar: 'ديوان ولي العهد', en: 'Crown Prince Court' },
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
        { ar: 'اتفاقية إيجار', en: 'Tenancy Agreement' },
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
        { ar: 'المستأجر', en: 'Tenant' },
        { ar: 'المؤجر', en: 'Lessor / Landlord' },
        { ar: 'قيمة الإيجار الشهري', en: 'Monthly Rental Value' },
        { ar: 'مبلغ الإيجار', en: 'Rent Amount' },
        { ar: 'الإيجار الشهري', en: 'Monthly Rent' },
        { ar: 'مدة العقد', en: 'Contract Duration' },
        { ar: 'تاريخ بدء العقد', en: 'Contract Start Date' },
        { ar: 'تاريخ انتهاء العقد', en: 'Contract End Date' },
        { ar: 'تاريخ التوقيع', en: 'Date of Signing' },
        { ar: 'تاريخ التحرير', en: 'Date of Execution' },
        { ar: 'يلتزم المستأجر', en: 'The Tenant undertakes' },
        { ar: 'يلتزم المؤجر', en: 'The Lessor undertakes' },
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
        { ar: 'الرصيد السابق', en: 'Previous Balance' },
        { ar: 'الرصيد الحالي', en: 'Current Balance' },
        { ar: 'تاريخ الاستحقاق', en: 'Due Date' },
        { ar: 'تم السداد', en: 'Paid' },
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

        // ── Correspondence & Classifications ──
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
        { ar: 'يرجى التكرم بالعلم', en: 'Kindly be informed' },
        { ar: 'يرجى التكرم بالموافقة', en: 'Kindly approve' },
        { ar: 'يرجى التكرم باتخاذ اللازم', en: 'Kindly take necessary action' },
        { ar: 'بالإشارة إلى الموضوع أعلاه', en: 'With reference to the above subject' },
        { ar: 'بالإشارة إلى الموضوع', en: 'With reference to the subject' },
        { ar: 'بالإشارة إلى كتابكم', en: 'With reference to your letter' },
        { ar: 'بالإشارة إلى خطابكم', en: 'With reference to your letter' },
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
        { ar: 'سنوياً', en: 'Annually' }
    ];
    ARABIC_PHRASES.sort((a, b) => b.ar.length - a.ar.length);

    // ── Word-Level Vocabulary Dictionary ──
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
        'مسكن': 'Residence', 'مساكن': 'Residences', 'سكن': 'Housing', 'سكني': 'Residential',
        'شقة': 'Flat', 'شقق': 'Apartments', 'مبنى': 'Building', 'مباني': 'Buildings', 'عمارة': 'Building',
        'وحدة': 'Unit', 'وحدات': 'Units', 'عقار': 'Property', 'عقارات': 'Properties',
        'غرفة': 'Room', 'غرف': 'Rooms', 'صالة': 'Hall', 'مطبخ': 'Kitchen', 'حمام': 'Bathroom',
        'كراج': 'Garage', 'موقف': 'Parking', 'حديقة': 'Garden', 'سطح': 'Roof', 'درج': 'Stairs', 'مدخل': 'Entrance',
        // Contract & Law
        'عقد': 'Contract', 'عقود': 'Contracts', 'اتفاق': 'Agreement', 'اتفاقية': 'Agreement',
        'طرف': 'Party', 'اطراف': 'Parties', 'أطراف': 'Parties', 'مؤجر': 'Lessor', 'مستأجر': 'Tenant',
        'ايجار': 'Rent', 'إيجار': 'Rent', 'اجرة': 'Rent Fee', 'أجرة': 'Rent Fee',
        'بدل': 'Allowance', 'تأمين': 'Security Deposit', 'استقطاع': 'Deduction', 'استقطاعات': 'Deductions',
        'قيمة': 'Value', 'مبلغ': 'Amount', 'مبالغ': 'Amounts', 'رصيد': 'Balance', 'حساب': 'Account',
        'شرط': 'Condition', 'شروط': 'Terms', 'بند': 'Clause', 'بنود': 'Clauses', 'مادة': 'Article', 'مواد': 'Articles',
        'قانون': 'Law', 'نظام': 'Regulation', 'لائحة': 'Bylaw', 'قرار': 'Decision', 'اوامر': 'Orders', 'أوامر': 'Orders',
        'التزام': 'Obligation', 'التزامات': 'Obligations', 'تعهد': 'Undertaking', 'تعهدات': 'Undertakings',
        'اخلاء': 'Eviction', 'إخلاء': 'Eviction', 'تسليم': 'Handover', 'استلام': 'Receipt',
        'صيانة': 'Maintenance', 'اصلاح': 'Repair', 'إصلاح': 'Repair', 'ترميم': 'Renovation',
        'تخصيص': 'Allocation', 'انتفاع': 'Occupancy', 'مستفيد': 'Beneficiary', 'مستفيدين': 'Beneficiaries',
        'فسخ': 'Termination', 'انهاء': 'Termination', 'إنهاء': 'Termination', 'تجديد': 'Renewal', 'تمديد': 'Extension',
        'سريان': 'Validity', 'انتهاء': 'Expiry', 'مهلة': 'Grace Period', 'فترة': 'Period', 'مدة': 'Duration',
        'غرامة': 'Penalty Fee', 'تاخير': 'Delay', 'تأخير': 'Delay', 'مخالفة': 'Violation', 'مخالفات': 'Violations',
        'ضرر': 'Damage', 'اضرار': 'Damages', 'أضرار': 'Damages', 'مسؤولية': 'Responsibility',
        // Official Document & Process
        'وثيقة': 'Document', 'وثائق': 'Documents', 'مستند': 'Document', 'مستندات': 'Documents',
        'خطاب': 'Letter', 'كتاب': 'Official Letter', 'رسالة': 'Letter', 'اشعار': 'Notice', 'إشعار': 'Notice',
        'انذار': 'Warning', 'إنذار': 'Warning', 'اخطار': 'Notification', 'إخطار': 'Notification',
        'محضر': 'Minutes / Record', 'تقرير': 'Report', 'كشف': 'Statement', 'بيان': 'Declaration',
        'استمارة': 'Form', 'طلب': 'Application', 'طلبات': 'Applications',
        'شهادة': 'Certificate', 'رخصة': 'Permit', 'بطاقة': 'Card', 'هوية': 'Identity', 'جواز': 'Passport',
        'رقم': 'No.', 'ارقام': 'Numbers', 'أرقام': 'Numbers', 'قيد': 'Registration', 'ملف': 'File',
        'صادر': 'Outgoing', 'وارد': 'Incoming', 'تاريخ': 'Date', 'تواريخ': 'Dates',
        'توقيع': 'Signature', 'توقيعات': 'Signatures', 'ختم': 'Stamp', 'اختام': 'Stamps', 'أختام': 'Stamps',
        'اعتماد': 'Approval', 'موافقة': 'Approval', 'رفض': 'Rejection', 'مرفق': 'Attachment', 'مرفقات': 'Attachments',
        'نسخة': 'Copy', 'صورة': 'Copy', 'اصل': 'Original', 'أصل': 'Original',
        // Government & Civil
        'مملكة': 'Kingdom', 'دولة': 'State', 'حكومة': 'Government', 'وزارة': 'Ministry', 'وزارات': 'Ministries',
        'ادارة': 'Directorate', 'إدارة': 'Directorate', 'فرع': 'Branch', 'فروع': 'Branches', 'قسم': 'Section',
        'لجنة': 'Committee', 'لجان': 'Committees', 'هيئة': 'Authority', 'مجلس': 'Council', 'ديوان': 'Court / Bureau',
        'محكمة': 'Court', 'قضاء': 'Judiciary', 'نيابة': 'Prosecution', 'شرطة': 'Police', 'امن': 'Security', 'أمن': 'Security',
        'دفاع': 'Defence', 'حرس': 'Guard', 'جيش': 'Army', 'عسكري': 'Military', 'مدني': 'Civilian',
        'موظف': 'Employee', 'موظفين': 'Employees', 'ضابط': 'Officer', 'ضباط': 'Officers', 'رتبة': 'Rank', 'رتب': 'Ranks',
        'رئيس': 'Head', 'مدير': 'Director', 'وكيل': 'Undersecretary', 'وزير': 'Minister', 'مقرر': 'Rapporteur',
        'باحث': 'Researcher', 'مستشار': 'Advisor', 'مهندس': 'Engineer', 'اخصائي': 'Specialist', 'أخصائي': 'Specialist',
        // Location & Geography
        'منطقة': 'Area', 'مناطق': 'Areas', 'محافظة': 'Governorate', 'بلدية': 'Municipality',
        'مدينة': 'City', 'قرية': 'Village', 'مجمع': 'Block', 'طريق': 'Road', 'شارع': 'Avenue',
        'جنوبية': 'Southern', 'شمالية': 'Northern', 'عاصمة': 'Capital', 'وسطى': 'Central',
        'سافرة': 'Safra', 'سافر': 'Safra', 'عوالي': 'Awali', 'رفاع': 'Riffa', 'منامة': 'Manama', 'محرق': 'Muharraq',
        // Financial & Utilities
        'كهرباء': 'Electricity', 'ماء': 'Water', 'مياه': 'Water', 'استهلاك': 'Consumption',
        'فاتورة': 'Bill', 'فواتير': 'Bills', 'عداد': 'Meter', 'قراءة': 'Reading',
        'سداد': 'Payment', 'دفع': 'Payment', 'مدفوع': 'Paid', 'مستحق': 'Due', 'متأخرات': 'Arrears',
        'بنك': 'Bank', 'مصرف': 'Bank', 'شيك': 'Cheque', 'راتب': 'Salary', 'رواتب': 'Salaries',
        'دينار': 'Dinar', 'فلس': 'Fils',
        // Common Verbs & Particles
        'يلتزم': 'undertakes', 'يتعهد': 'pledges', 'يقر': 'declares', 'يوافق': 'agrees',
        'يدفع': 'pays', 'يسدد': 'settles', 'يستلم': 'receives', 'يسلم': 'hands over',
        'يخلي': 'vacates', 'يحافظ': 'preserves', 'يخطر': 'notifies', 'ينذر': 'warns',
        'يوقع': 'signs', 'يعتمد': 'approves', 'يعتبر': 'is considered', 'يجوز': 'may', 'يحظر': 'is prohibited',
        'يجب': 'shall', 'ينبغي': 'should', 'تم': 'completed', 'صدر': 'issued', 'ورد': 'received',
        'في': 'in', 'على': 'on', 'إلى': 'to', 'الى': 'to', 'من': 'from', 'عن': 'about',
        'مع': 'with', 'بين': 'between', 'لدى': 'with', 'حتى': 'until', 'منذ': 'since',
        'بعد': 'after', 'قبل': 'before', 'تحت': 'under', 'فوق': 'above', 'امام': 'in front of', 'أمام': 'in front of',
        'خلف': 'behind', 'داخل': 'inside', 'خارج': 'outside', 'خلال': 'during',
        'هذا': 'this', 'هذه': 'this', 'ذلك': 'that', 'تلك': 'that', 'هؤلاء': 'these',
        'هو': 'he', 'هي': 'she', 'هم': 'they', 'نحن': 'we', 'انا': 'I', 'أنا': 'I',
        'الذي': 'which', 'التي': 'which', 'الذين': 'who',
        'كل': 'every', 'جميع': 'all', 'بعض': 'some', 'غير': 'non / other', 'دون': 'without', 'بدون': 'without',
        'فقط': 'only', 'ايضا': 'also', 'أيضاً': 'also', 'حسب': 'according to', 'وفق': 'according to', 'بموجب': 'pursuant to',
        'الاول': 'First', 'الأول': 'First', 'اول': 'first', 'أول': 'first',
        'الثاني': 'Second', 'ثاني': 'second',
        'الثالث': 'Third', 'ثالث': 'third',
        'الرابع': 'Fourth', 'رابع': 'fourth',
        'الخامس': 'Fifth', 'خامس': 'fifth'
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

    // ── Phonetic Transliteration Fallback ──
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
        const clean = word.replace(/[\u064B-\u0652\u0670\u0640]/g, '');
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
        if (ARABIC_WORDS[stem]) return ARABIC_WORDS[stem];
        if (ARABIC_NAMES[stem]) return ARABIC_NAMES[stem];
        const stemNorm = stem.replace(/[\u064B-\u0652\u0670\u0640]/g, '').replace(/[إأآ]/g, 'ا').replace(/ة$/g, 'ه');
        if (ARABIC_WORDS[stemNorm]) return ARABIC_WORDS[stemNorm];
        if (ARABIC_NAMES[stemNorm]) return ARABIC_NAMES[stemNorm];
        if (stem.endsWith('ت')) {
            const withTaa = stem.slice(0, -1) + 'ة';
            const withHaa = stem.slice(0, -1) + 'ه';
            if (ARABIC_WORDS[withTaa]) return ARABIC_WORDS[withTaa];
            if (ARABIC_WORDS[withHaa]) return ARABIC_WORDS[withHaa];
        }
        return null;
    }

    function translateArabicWord(rawWord) {
        if (!rawWord || typeof rawWord !== 'string') return '';
        const word = rawWord.trim();
        if (!word) return '';

        // Separate attached punctuation: e.g. "(المستأجر)" -> prefix "(", core "المستأجر", suffix ")"
        const m = word.match(/^([^\u0600-\u06FFA-Za-z0-9]*)([\u0600-\u06FF]+)([^\u0600-\u06FFA-Za-z0-9]*)$/);
        if (!m) {
            const direct = lookupArabicStem(word);
            return direct ? direct : transliterateArabic(word);
        }

        const prefixPunct = m[1] || '';
        const coreArabic = m[2];
        const suffixPunct = m[3] || '';

        // 1. Direct match
        const directCore = lookupArabicStem(coreArabic);
        if (directCore) {
            return prefixPunct + directCore + suffixPunct;
        }

        // 2. Morphological decomposition
        const prefixes = [
            { ar: 'وال', en: 'and the ' },
            { ar: 'فال', en: 'and the ' },
            { ar: 'بال', en: 'in the ' },
            { ar: 'ولل', en: 'and for the ' },
            { ar: 'لل', en: 'for the ' },
            { ar: 'كال', en: 'as the ' },
            { ar: 'ال', en: 'the ' },
            { ar: 'و', en: 'and ' },
            { ar: 'ف', en: 'then ' },
            { ar: 'ب', en: 'by ' },
            { ar: 'ل', en: 'to ' }
        ];

        const suffixes = [
            { ar: 'هما', en: ' their' },
            { ar: 'هم', en: ' their' },
            { ar: 'هن', en: ' their' },
            { ar: 'كم', en: ' your' },
            { ar: 'نا', en: ' our' },
            { ar: 'ها', en: ' its' },
            { ar: 'ه', en: ' his' },
            { ar: 'ي', en: ' my' },
            { ar: 'ين', en: '' },
            { ar: 'ون', en: '' },
            { ar: 'ات', en: '' },
            { ar: 'ية', en: '' }
        ];

        // Try prefix only
        for (const p of prefixes) {
            if (coreArabic.startsWith(p.ar) && coreArabic.length > p.ar.length + 1) {
                const stem = coreArabic.slice(p.ar.length);
                const stemMatch = lookupArabicStem(stem);
                if (stemMatch) {
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

        // 1. Convert Eastern Arabic numerals to Western digits
        const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        arabicNumerals.forEach((ch, idx) => {
            result = result.replaceAll(ch, String(idx));
        });

        // 2. Normalize Arabic punctuation
        result = result
            .replaceAll('،', ', ')
            .replaceAll('؛', '; ')
            .replaceAll('؟', '? ');

        // 3. Multi-word phrase and entity replacements (longest first, boundary-aware)
        for (const item of ARABIC_PHRASES) {
            if (!item.ar) continue;
            const escaped = item.ar.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`(^|[^\\u0600-\\u06FFA-Za-z0-9])${escaped}(?=[^\\u0600-\\u06FFA-Za-z0-9]|$)`, 'g');
            result = result.replace(regex, (match, p1) => `${p1}${item.en}`);
        }

        // 4. Tokenize remaining words and translate individual Arabic words/names/stems
        if (/[\u0600-\u06FF]/.test(result)) {
            const tokens = result.split(/(\s+|[,;:\-–—\(\)\[\]"'\/\\]+)/);
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

                const worker = await Tesseract.createWorker('ara', 1, {
                    workerPath: `${basePath}/worker.min.js`,
                    corePath: `${basePath}/tesseract-core-simd-lstm.wasm.js`,
                    langPath: basePath,
                    gzip: true
                });
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
        for (const it of items) {
            if (!it.str || !it.str.trim()) continue;
            const tx = it.transform || [1, 0, 0, 1, 0, 0];
            const h = it.height || 14;
            const w = it.width || (it.str.length * (h * 0.55));
            const x0 = tx[4];
            const y0 = Math.max(0, viewportHeight - tx[5] - h);
            const x1 = x0 + w;
            const y1 = y0 + h;
            valid.push({
                str: it.str,
                x0, y0, x1, y1, h, w
            });
        }
        if (valid.length === 0) return [];

        // Sort by vertical position (top to bottom)
        valid.sort((a, b) => a.y0 - b.y0);

        const clusters = [];
        for (const item of valid) {
            // Group items whose vertical baseline is within 6px or 50% line height
            const cluster = clusters.find(c => Math.abs(c.y0 - item.y0) <= Math.max(6, item.h * 0.5));
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

        const lines = [];
        for (const cluster of clusters) {
            const lineText = cluster.items.map(it => it.str).join(' ').replace(/\s+/g, ' ').trim();
            if (lineText.length > 0) {
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

        const canvas = pageWrapper.querySelector('canvas.pdf-page-canvas');

        // 1. Digital text layer from PDF.js if available
        if (pdfDoc) {
            try {
                const page = await pdfDoc.getPage(pageNum);
                const viewport = page.getViewport({ scale: 1.0 });
                const textContent = await page.getTextContent();
                if (textContent && textContent.items && textContent.items.length > 0) {
                    const arabicItems = textContent.items.filter(it => it.str && /[\u0600-\u06FF]/.test(it.str));
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

        // 2. Client-side Offline OCR via Local Tesseract.js
        if (canvas && typeof Tesseract !== 'undefined') {
            const indicator = document.createElement('div');
            indicator.className = 'ocr-scanning-indicator absolute top-3 left-3 px-3 py-1.5 rounded-xl bg-slate-900/85 text-white backdrop-blur-xs text-xs flex items-center gap-2 shadow-lg z-30 pointer-events-none animate-pulse';
            indicator.innerHTML = `
                <svg class="w-3.5 h-3.5 animate-spin text-blue-400 flex-shrink-0" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                <span>Translating scan (Offline OCR)...</span>
            `;
            pageWrapper.appendChild(indicator);

            try {
                const worker = await getTesseractWorker();
                if (worker) {
                    const res = await worker.recognize(canvas);
                    if (res && res.data && res.data.lines && res.data.lines.length > 0) {
                        const lines = res.data.lines
                            .filter(l => l.text && l.text.trim().length > 0)
                            .map(l => ({
                                text: l.text.trim(),
                                bbox: l.bbox,
                                words: l.words
                            }));
                        if (lines.length > 0) {
                            pageOcrCache.set(cacheKey, lines);
                            indicator.remove();
                            return lines;
                        }
                    }
                }
            } catch (err) {
                console.error('Tesseract offline OCR error:', err);
            } finally {
                indicator.remove();
            }
        }

        // 3. Fallback: Database metadata if present
        const meta = await fetchDocumentMetadata(vaultId);
        if (meta && meta.pages && meta.pages.length > 0) {
            const p = meta.pages.find(x => (x.page_number || x.pageNumber) === pageNum);
            if (p) {
                const lines = [];
                const cW = canvas ? (canvas.clientWidth || canvas.width || 600) : 600;
                if (p.subject) {
                    lines.push({
                        text: p.subject,
                        bbox: { x0: 40, y0: 60, x1: cW - 40, y1: 95 }
                    });
                }
                if (p.sender) {
                    lines.push({
                        text: p.sender,
                        bbox: { x0: 40, y0: 105, x1: Math.round(cW * 0.5), y1: 130 }
                    });
                }
                if (p.content_explanation) {
                    lines.push({
                        text: p.content_explanation,
                        bbox: { x0: 40, y0: 145, x1: cW - 40, y1: 220 }
                    });
                }
                if (lines.length > 0) {
                    pageOcrCache.set(cacheKey, lines);
                    return lines;
                }
            }
        }

        return [];
    }

    async function renderPageTranslationLayer(pageWrapper, pageNum, vaultId) {
        if (!pageWrapper) return;
        const canvas = pageWrapper.querySelector('canvas.pdf-page-canvas');
        if (!canvas) return;

        let layer = pageWrapper.querySelector(`.pdf-translation-layer[data-page-number="${pageNum}"]`);
        if (!layer) {
            layer = document.createElement('div');
            layer.className = 'pdf-translation-layer absolute inset-0 pointer-events-auto z-10 select-text';
            layer.setAttribute('data-page-number', pageNum);
            pageWrapper.appendChild(layer);
        }

        layer.innerHTML = '';

        const lines = await detectPageText(pageWrapper, pageNum, vaultId, currentPdfDoc);
        if (!lines || lines.length === 0) {
            return;
        }

        const canvasCssWidth = parseFloat(canvas.style.width) || canvas.clientWidth || canvas.width;
        const canvasCssHeight = parseFloat(canvas.style.height) || canvas.clientHeight || canvas.height;
        const scaleRatioX = canvasCssWidth / (canvas.width || canvasCssWidth);
        const scaleRatioY = canvasCssHeight / (canvas.height || canvasCssHeight);

        let renderedBoxesCount = 0;
        lines.forEach(line => {
            if (!line || !line.text) return;
            const origText = line.text.trim();
            if (!origText || origText.length < 1) return;

            const hasArabic = /[\u0600-\u06FF]/.test(origText);
            const translated = hasArabic ? translateArabicText(origText) : origText;
            if (!translated || !translated.trim()) return;

            const bbox = line.bbox || { x0: 0, y0: 0, x1: 100, y1: 30 };
            const rawX0 = (bbox.x0 !== undefined) ? bbox.x0 : (bbox.left !== undefined ? bbox.left : 0);
            const rawY0 = (bbox.y0 !== undefined) ? bbox.y0 : (bbox.top !== undefined ? bbox.top : 0);
            const rawX1 = (bbox.x1 !== undefined) ? bbox.x1 : (bbox.right !== undefined ? bbox.right : (rawX0 + (bbox.width || 0)));
            const rawY1 = (bbox.y1 !== undefined) ? bbox.y1 : (bbox.bottom !== undefined ? bbox.bottom : (rawY0 + (bbox.height || 0)));

            const left = Math.max(0, rawX0 * scaleRatioX);
            const top = Math.max(0, rawY0 * scaleRatioY);
            const width = Math.max(30, (rawX1 - rawX0) * scaleRatioX);
            const height = Math.max(16, (rawY1 - rawY0) * scaleRatioY);

            const fontSize = Math.max(10, Math.min(Math.round(height * 0.72), 22));

            const box = document.createElement('div');
            box.className = 'in-place-translated-box';
            box.setAttribute('data-original-text', origText);
            box.setAttribute('title', `Original: ${origText}\nClick or hover to peek scan`);
            box.textContent = translated;

            box.style.position = 'absolute';
            box.style.left = `${Math.round(left)}px`;
            box.style.top = `${Math.round(top)}px`;
            box.style.width = `${Math.round(width)}px`;
            box.style.height = `${Math.round(height)}px`;
            box.style.fontSize = `${fontSize}px`;
            box.style.backgroundColor = '#ffffff';
            box.style.color = '#0f172a';
            box.style.display = 'flex';
            box.style.alignItems = 'center';
            box.style.justifyContent = 'flex-start';
            box.style.padding = '0 4px';
            box.style.boxSizing = 'border-box';
            box.style.overflow = 'hidden';
            box.style.textOverflow = 'ellipsis';
            box.style.whiteSpace = 'nowrap';
            box.style.fontFamily = 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            box.style.fontWeight = '500';
            box.style.lineHeight = '1.15';
            box.style.borderRadius = '2px';
            box.style.boxShadow = '0 1px 2px rgba(0,0,0,0.08)';
            box.style.zIndex = '10';
            box.style.transition = 'opacity 0.15s ease';
            box.style.cursor = 'pointer';
            box.style.userSelect = 'text';

            box.addEventListener('mouseenter', () => { box.style.opacity = '0.12'; });
            box.addEventListener('mouseleave', () => { box.style.opacity = '1'; });
            box.addEventListener('click', (e) => {
                e.stopPropagation();
                box.style.opacity = (box.style.opacity === '0.12' ? '1' : '0.12');
            });

            layer.appendChild(box);
            renderedBoxesCount++;
        });

        if (renderedBoxesCount > 0) {
            const peekBtn = document.createElement('button');
            peekBtn.type = 'button';
            peekBtn.className = 'btn-peek-scan absolute top-2 left-2 px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-900/85 hover:bg-blue-800 text-white backdrop-blur-xs z-20 cursor-pointer shadow-xs transition-all flex items-center gap-1.5 select-none';
            peekBtn.title = 'Hold or click to peek at original Arabic scan • انقر لمعاينة المسح الأصلي';
            peekBtn.innerHTML = `
                <svg class="w-3.5 h-3.5 text-blue-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                <span>Peek Original</span>
            `;

            let isPeeking = false;
            const applyPeekState = (peeking) => {
                layer.querySelectorAll('.in-place-translated-box').forEach(b => {
                    b.style.opacity = peeking ? '0' : '1';
                });
                if (peeking) {
                    peekBtn.classList.add('bg-blue-600');
                    peekBtn.classList.remove('bg-blue-900/85');
                } else {
                    peekBtn.classList.remove('bg-blue-600');
                    peekBtn.classList.add('bg-blue-900/85');
                }
            };

            peekBtn.addEventListener('pointerdown', () => applyPeekState(true));
            peekBtn.addEventListener('pointerup', () => { if (!isPeeking) applyPeekState(false); });
            peekBtn.addEventListener('pointerleave', () => { if (!isPeeking) applyPeekState(false); });
            peekBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                isPeeking = !isPeeking;
                applyPeekState(isPeeking);
            });

            layer.appendChild(peekBtn);
        }
    }

    let currentTranslationPromise = null;

    async function renderDocumentTranslation() {
        if (!currentPinnedDoc || !currentPinnedDoc.vaultId) return;
        const vaultId = currentPinnedDoc.vaultId;
        const pdfUrl = resolvePdfUrl(vaultId);

        if (currentTranslationPromise) {
            return currentTranslationPromise;
        }

        currentTranslationPromise = (async () => {
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
            if (!currentPdfDoc || currentPdfUrl !== pdfUrl || wrappers.length === 0) {
                await renderPdfDocument(pdfUrl);
            }

            if (!isTranslationActive || !currentPinnedDoc || currentPinnedDoc.vaultId !== vaultId) {
                return;
            }

            const freshWrappers = canvasContainer ? canvasContainer.querySelectorAll('.pdf-page-wrapper') : [];
            for (let i = 0; i < freshWrappers.length; i++) {
                const pageWrapper = freshWrappers[i];
                const pageNum = parseInt(pageWrapper.getAttribute('data-page-number') || String(i + 1), 10);
                await renderPageTranslationLayer(pageWrapper, pageNum, vaultId);
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

        // Touchscreen / Tablet auto-detection:
        // Android, iOS (iPhone/iPad), tablets, or touch-first devices where iframe PDFs prompt downloads
        if (typeof navigator !== 'undefined') {
            const ua = navigator.userAgent || '';
            const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet/i.test(ua);
            const isTouchScreen = (navigator.maxTouchPoints > 0 || (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(pointer: coarse)').matches));
            const isIPad = /Macintosh/i.test(ua) && navigator.maxTouchPoints > 1;

            if (isMobileUA || isIPad || isTouchScreen) return true;

            // Fallback for devices without native PDF viewer plugin
            if (navigator.pdfViewerEnabled === false) return true;
        }

        // Default for computer: native iframe (ensures desktop plugins & PDF viewers work)
        return false;
    }

    function shouldUseCanvasViewer() {
        return shouldUseOfficialViewer();
    }

    function resolveViewerSrc(pdfUrl) {
        if (shouldUseOfficialViewer()) {
            return `/lib/pdfjs/web/viewer.html?file=${encodeURIComponent(pdfUrl)}`;
        }
        return pdfUrl + '#view=FitH';
    }

    function loadPdfIntoFrame(pdfFrame, pdfUrl) {
        if (!pdfFrame) return;
        const targetSrc = resolveViewerSrc(pdfUrl);

        let reusedViewer = false;
        if (shouldUseOfficialViewer()) {
            try {
                const frameWin = pdfFrame.contentWindow;
                if (frameWin && frameWin.PDFViewerApplication && frameWin.PDFViewerApplication.initialized && typeof frameWin.PDFViewerApplication.open === 'function') {
                    frameWin.PDFViewerApplication.open({ url: pdfUrl });
                    reusedViewer = true;
                }
            } catch (e) {
                reusedViewer = false;
            }
        }

        if (!reusedViewer && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
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
            const pdf = await currentLoadingTask.promise;
            currentPdfDoc = pdf;
            currentPdfUrl = pdfUrl;

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
            if (pdfError) {
                pdfError.classList.remove('hidden');
                const errMsg = document.getElementById('pdf-viewer-error-msg');
                if (errMsg) errMsg.textContent = err.message || 'Error loading PDF';
                const fallbackLink = document.getElementById('pdf-viewer-fallback-link');
                if (fallbackLink) fallbackLink.href = pdfUrl;
            }
            // If PDF.js fails to render, show iframe fallback
            if (pdfFrame) pdfFrame.classList.remove('hidden');
        } finally {
            if (pdfLoading) pdfLoading.classList.add('hidden');
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
    window.transliterateArabic = transliterateArabic;
    window.clusterPdfItemsIntoLines = clusterPdfItemsIntoLines;
    window.getEnglishCategory = getEnglishCategory;
    window.updateTranslationButtonState = updateTranslationButtonState;
})();
