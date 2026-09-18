<?php
declare(strict_types=1);

const CONTACT_RECIPIENT = 'info@ai-experts.network';
const CONTACT_SENDER = 'info@ai-experts.network';

header('Content-Type: application/json; charset=UTF-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

function respond(int $status, bool $success, string $message): void
{
    http_response_code($status);
    echo json_encode(
        ['success' => $success, 'message' => $message],
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
    );
    exit;
}

function scalar_value(string $key, int $maxLength): string
{
    $value = $_POST[$key] ?? '';
    if (!is_string($value)) {
        return '';
    }

    $value = trim(preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $value) ?? '');
    return mb_substr($value, 0, $maxLength, 'UTF-8');
}

function list_value(string $key, int $maxItems = 20): array
{
    $value = $_POST[$key] ?? [];
    if (is_string($value)) {
        $value = [$value];
    }
    if (!is_array($value)) {
        return [];
    }

    $items = [];
    foreach (array_slice($value, 0, $maxItems) as $item) {
        if (is_string($item)) {
            $clean = trim(preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $item) ?? '');
            if ($clean !== '') {
                $items[] = mb_substr($clean, 0, 500, 'UTF-8');
            }
        }
    }
    return $items;
}

function safe_header_value(string $value): string
{
    return trim(str_replace(["\r", "\n"], ' ', $value));
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    respond(405, false, 'Method not allowed.');
}

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $originHost = strtolower((string) parse_url($origin, PHP_URL_HOST));
    if (!in_array($originHost, ['ai-experts.network', 'www.ai-experts.network', 'localhost', '127.0.0.1'], true)) {
        respond(403, false, 'Request origin not allowed.');
    }
}

// Bots often fill this visually hidden field. Return success without sending mail.
if (scalar_value('website', 200) !== '') {
    respond(200, true, 'Message accepted.');
}

$startedAt = (int) scalar_value('form_started_at', 20);
$elapsedMs = $startedAt > 0 ? ((int) round(microtime(true) * 1000)) - $startedAt : 0;
if ($startedAt <= 0 || $elapsedMs < 1500 || $elapsedMs > 86400000) {
    respond(422, false, 'Invalid form timing.');
}

$name = scalar_value('full-name', 120);
$email = scalar_value('email', 254);
$company = scalar_value('unternehmen', 200);
$message = scalar_value('message', 5000);
$language = scalar_value('trp-form-language', 5) === 'en' ? 'en' : 'de';
$formId = scalar_value('_wpcf7', 20);

if (
    $name === ''
    || $email === ''
    || !filter_var($email, FILTER_VALIDATE_EMAIL)
    || ($formId === '214' && $company === '')
) {
    respond(422, false, $language === 'en'
        ? 'Please complete all required fields and enter a valid email address.'
        : 'Bitte füllen Sie alle Pflichtfelder aus und geben Sie eine gültige E-Mail-Adresse ein.');
}

$fields = [
    'Anfragetyp / Request type' => scalar_value('help-que', 200),
    'Ausgewähltes Mitglied / Selected member' => scalar_value('teams', 200),
    'Name' => $name,
    'E-Mail' => $email,
    'Unternehmen / Company' => $company,
    'Nachricht / Message' => $message,
    'KI-Integration / AI integration' => list_value('questionnaire-first'),
    'Mitgliedschaft / Membership' => list_value('questionnaire-sec'),
    'Gewünschte Unterstützung / Requested support' => list_value('specific-ai-list'),
    'KI-Ausgangslage / AI starting point' => list_value('ai-list'),
];

$lines = [
    'Neue Kontaktanfrage über ai-experts.network',
    '============================================',
    '',
];
foreach ($fields as $label => $value) {
    if (is_array($value)) {
        if ($value === []) {
            continue;
        }
        $lines[] = $label . ':';
        foreach ($value as $item) {
            $lines[] = '  - ' . $item;
        }
        $lines[] = '';
        continue;
    }
    if ($value !== '') {
        $lines[] = $label . ':';
        $lines[] = $value;
        $lines[] = '';
    }
}

$lines[] = 'Technische Angaben:';
$lines[] = 'Sprache: ' . strtoupper($language);
$lines[] = 'Formular-ID: ' . $formId;
$lines[] = 'Quellseite: ' . scalar_value('source_page', 500);
$lines[] = 'Zeitpunkt: ' . date('c');

$safeName = safe_header_value($name);
$subject = 'Neue Kontakt - Message von ' . $safeName;
$encodedSubject = mb_encode_mimeheader($subject, 'UTF-8', 'B', "\r\n");
$headers = [
    'From: AI Experts Website <' . CONTACT_SENDER . '>',
    'Reply-To: ' . safe_header_value($email),
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'X-Mailer: AI Experts Contact Form',
];

$sent = mail(
    CONTACT_RECIPIENT,
    $encodedSubject,
    implode("\r\n", $lines),
    implode("\r\n", $headers)
);

if (!$sent) {
    error_log('AI Experts contact form: PHP mail() failed.');
    respond(500, false, $language === 'en'
        ? 'The message could not be sent.'
        : 'Die Nachricht konnte nicht gesendet werden.');
}

respond(200, true, $language === 'en'
    ? 'Your message has been sent.'
    : 'Ihre Nachricht wurde gesendet.');
