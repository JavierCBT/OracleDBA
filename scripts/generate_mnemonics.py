import json
import os
import re
import itertools

COMMON_ORACLE_GENERIC_WORDS = {
    # Adverbs, quantifiers, prepositions, conjunctions
    'only', 'all', 'both', 'either', 'neither', 'always', 'never', 'also', 'just', 'even',
    'each', 'every', 'some', 'any', 'many', 'more', 'most', 'less', 'few', 'none', 'not', 'no', 'nor',
    'can', 'may', 'must', 'shall', 'should', 'will', 'would', 'could', 'might',
    'be', 'been', 'being', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did', 'done',
    'a', 'an', 'the', 'this', 'that', 'these', 'those', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'with',
    'from', 'into', 'onto', 'than', 'then', 'so', 'such', 'if', 'but', 'or', 'and',
    
    # Generic SQL / DB terms that should not be isolated 1-word mnemonics
    'sql', 'database', 'drop', 'set', 'image', 'bin', 'keep', 'mount', 'current', 'upgrade',
    'system', 'table', 'tables', 'tablespace', 'tablespaces', 'file', 'files', 'data',
    'block', 'blocks', 'row', 'rows', 'column', 'columns', 'user', 'users', 'role', 'roles',
    'grant', 'grants', 'cache', 'unix', 'pluggable', 'container', 'root', 'seed', 'instance',
    'instances', 'node', 'nodes', 'cluster', 'clusters', 'service', 'services', 'disk', 'disks',
    'group', 'groups', 'pool', 'pools', 'memory', 'session', 'sessions', 'process', 'processes',
    'log', 'logs', 'redo', 'undo', 'error', 'errors', 'status', 'state', 'mode', 'type', 'name',
    'time', 'date', 'size', 'value', 'values', 'clause', 'clauses', 'option', 'options',
    'command', 'commands', 'statement', 'statements', 'view', 'views', 'schema', 'schemas',
    'backup', 'backups', 'restore', 'restores', 'recovery', 'recover', 'flashback', 'advisor',
    'create', 'creating', 'created', 'delete', 'deleting', 'deleted', 'alter', 'altering', 'altered',
    'select', 'insert', 'update', 'truncate', 'commit', 'rollback', 'savepoint',
    'open', 'closed', 'online', 'offline', 'active', 'inactive', 'true', 'false', 'correct', 'incorrect',
    'failed', 'fails', 'successful', 'success', 'required', 'requires', 'optional', 'manually', 'automatically'
}

ALLOWED_TECHNICAL_SINGLE_WORDS = {
    # Specific utilities / daemons / tools
    'oclumon', 'osysmond', 'ologgerd', 'crsd', 'evmd', 'cssd', 'gimr', 'srvctl',
    'asmcmd', 'crsctl', 'cluvfy', 'ocrdump', 'ocrcheck', 'ocrconfig', 'advm', 'acfs',
    'dbca', 'dbua', 'oui', 'roohctl', 'appvipcfg', 'orapwd', 'adrci',
    
    # OS Groups / Privileges / Special technology terms
    'osasm', 'osdba', 'scan', 'gns', 'spfile', 'fra', 'sga', 'pga', 'uga',
    'archivelog', 'noarchivelog', 'omf', 'recyclebin', 'autoupgrade', 'preupgrade',
    'multisection', 'sharding', 'colocation_tag', 'quiesced'
}

ACTION_VERBS = {
    'create', 'creating', 'created', 'direct', 'directing', 'directed', 'route', 'routes',
    'routing', 'routed', 'reduce', 'reduces', 'reducing', 'reduced', 'increase', 'increases',
    'increasing', 'increased', 'manage', 'manages', 'managing', 'managed', 'mount', 'mounting',
    'mounted', 'recover', 'recovers', 'recovering', 'recovered', 'restore', 'restores',
    'restoring', 'restored', 'convert', 'converts', 'converting', 'converted', 'tune', 'tunes',
    'tuning', 'tuned', 'generate', 'generates', 'generating', 'generated', 'specify',
    'specifying', 'specified', 'prompt', 'prompts', 'prompting', 'prompted', 'reassign',
    'reassigns', 'reassigned', 'allocate', 'allocates', 'allocated', 'isolate', 'isolates',
    'isolated', 'evict', 'evicts', 'evicted', 'stop', 'stops', 'stopped', 'start', 'starts',
    'started', 'using', 'use', 'uses'
}

def is_technical_single_word(w):
    wl = w.lower().strip('.,;:()[]"\'')
    if wl in COMMON_ORACLE_GENERIC_WORDS:
        return False
    if '_' in w or '$' in w: return True
    if '.' in w and not w.endswith('.'): return True
    if any(c.isdigit() for c in w) and len(w) >= 3: return True
    if wl in ALLOWED_TECHNICAL_SINGLE_WORDS: return True
    return False

MANUAL_OVERRIDES = {
    # ==================== 1z0-078 ====================
    (78, 1): ["is stopped on all nodes.", "started on HOST01", "is started on all nodes."],
    (78, 2): ["oclumon", "osysmond"],
    (78, 3): ["Oracle RAC Resource Runtime Management"],
    (78, 4): ["out-of-place patching of Oracle Grid Infrastructure 19c", "system commands including ACFS, AFD, OLFS, and OKA are not updated", "automatically run the root.sh script"],
    (78, 5): ["VIPs for the node being patched are relocated to another node"],
    (78, 6): ["cannot directly modify the policy set when Quality of Service (QoS) Management is used", "different attributes defined for different policies in the policy set", "same attributes defined for different policies in the policy set"],
    (78, 7): ["redundancy is lowered", "changes to allocation units are tracked"],
    (78, 8): ["thread of redo must be created before starting a fourth instance", "thread of redo must contain at least two log groups"],
    (78, 9): ["delete node -n host04 command as root on host01", "rootcrs.pl -deconfig -force command as root on host04"],
    (78, 10): ["across RAC database instances", "SCAN listeners", "client, the listener, or both"],
    (78, 11): ["local temporary tablespaces", "open one, several, or all PDBs", "UNDO tablespace for each instance"],
    (78, 12): ["do not need to make any configuration changes"],
    (78, 13): ["different outputs depending on the instance type", "seen in v$fixed_table"],
    (78, 14): ["one ORACLE_HOME only on the first cluster node"],
    (78, 15): ["Clusterware stack must be up on all cluster nodes where", "Grid Infrastructure must be installed on all cluster nodes where"],
    (78, 16): ["appvipcfg utility", "created with the crsctl utility"],
    (78, 18): ["separate administrator-defined categories", "same Oracle-supplied category"],
    (78, 19): ["newtemplate must be defined", "subdirectories ORCL and USERS must already exist"],
    (78, 20): ["cannot be used to automate the opening", "not automatically registered in the OCR"],
    (78, 21): ["Database block buffers", "Cursors", "Enqueues"],
    (78, 22): ["start automatically in observer mode", "Deactivate network time protocol (NTP)"],
    (78, 23): ["shuts down the ASM instance on HOST03", "reconnected to the ASM instance on HOST02", "reconnected to the ASM instance on HOST01"],
    (78, 24): ["fail over to any other available CDB1 instance in prod_pool", "available on any one available CDB1 instance in prod_pool at any one time"],
    (78, 25): ["automatically stopped to comply", "initially inactive", "reassigned to server pools"],
    (78, 26): ["crsctl set trace res", "crsctl set log res"],
    (78, 27): ["CLUVFY", "OCRDUMP"],
    (78, 28): ["started manually using crsctl"],
    (78, 29): ["disjoint subset of rows", "direct all branches", "block pings"],
    (78, 30): ["Using DBCA to create a template"],
    (78, 31): ["READ ONLY mode", "CREATE PLUGGABLE DATABASE system privilege", "PDB_FILE_NAME_CONVERT"],
    (78, 32): ["compatibility attribute for ADVM must be set to 12.1 or higher"],
    (78, 33): ["storage shared across all hub nodes", "Hub nodes require direct access to the OCR file", "Hub nodes require direct access to the voting disks"],
    (78, 34): ["cluvfy.sh can verify that the cluster is ready for an upgrade", "cluvfy.sh can generate fixup scripts", "Oracle Universal Installer which in turn invokes the built-in cluster verification utility", "upgrade must be done out-of-place"],
    (78, 35): ["require a quorum failgroup", "creation of a disk group for use by the voting disks and OCR file"],
    (78, 36): ["Set COMPATIBLE.ASM to 12.1, COMPATIBLE.RDBMS to 11.2, and COMPATIBLE.ADVM to 12.1."],
    (78, 37): ["policy managed for a multitenant database", "creation of a new server pool using DBCA", "administrator managed for a multitenant database"],
    (78, 38): ["read I/O directly to ASM Disks", "Database instances can write metadata", "ASM instances can write metadata"],
    (78, 39): ["fall back to a preferred instance when it becomes available after it was failed over"],
    (78, 40): ["2 = TRANSACTIONAL", "2 = IMMEDIATE"],
    (78, 41): ["same size for optimal performance", "same hardware specifications and storage attributes"],
    (78, 42): ["ACFS auditing information is replicated", "host both primary and standby file systems"],
    (78, 43): ["relocated to one or more surviving hub nodes", "Sessions connected to the failed node could be relocated", "node is evicted from the cluster"],
    (78, 44): ["routed to the same instance that offers a given service"],
    (78, 45): ["SSH user equivalence", "Fix-up scripts generated during the installation", "RAC installations require Oracle Enterprise Edition", "installed into an ACFS file system"],
    (78, 46): ["ASM_POWER_LIMIT is 1024", "ASM_DISKGROUPS parameter is optional"],
    (78, 47): ["dynamically assign a newly created undo tablespace", "OMF is enabled", "instance recovery can write to the undo tablespace"],
    (78, 48): ["requires Oracle Grid Infrastructure", "managed by QoS even if it does have database instances", "administrator managed or policy managed", "multiple databases assigned to the same server pool"],
    (78, 49): ["not encrypted unless it is created in an encrypted directory", "ACFS snapshot can be ACFS encrypted", "acfsutil encr on"],
    (78, 50): ["Shadow GRD resources may exist in more than one database instance", "Clustered ASM has GRD resources distributed among all ASM instances", "stored in the shared pool of each instance"],
    (78, 51): ["Server-side connect time load balancing is done at the time of the initial connection attempt", "Client-side connect time load balancing is done at the time of the initial connection attempt"],
    (78, 52): ["skew in response time", "data captured on all instances", "latency problems in the Cluster Interconnect"],
    (78, 53): ["characteristics of the underlying ASM disks", "case of cluster node failure"],
    (78, 54): ["Cluster resources", "Local resources", "Administrator-defined resources"],
    (78, 55): ["Grid Naming Service is optional", "three voting files regardless of the number of failgroups"],
    (78, 56): ["an application resource"],
    (78, 57): ["ASM Cluster File System (ACFS) can be deployed on any nodes", "client of an ASM instance running on any node", "ASM instance and database instances can coexist"],
    (78, 58): ["1, 2, 3, 4 and 6."],
    (78, 59): ["acfsutil audit read", "acfsutil audit init", "acfsutil audit purge"],
    (78, 60): ["High availability for the CRM service", "High availability for the ERP service", "ERP across three Single Client Access Name (SCAN) listeners", "CRM across all database instances running on servers in the prod pool"],
    (78, 61): ["multiple library caches for the same stored procedure", "sequence created with the CACHE and ORDER clauses"],
    (78, 62): ["converters and waiters in the same instance", "owners and waiters in the same instance"],
    (78, 63): ["One ASM instance is shut down and the instance count is reduced by one"],
    (78, 64): ["Archive logs", "Data files for tablespaces", "Oracle database executables"],
    (78, 65): ["crsctl query css votedisk", "cat /etc/oracle/ocr.loc"],
    (78, 66): ["REDUNDANCY attribute set to HIGH", "three copies for each allocation unit", "MIRROR will have three-way mirroring"],
    (78, 67): ["Single Client Access Name (SCAN) virtual IP addresses (VIPs)"],
    (78, 68): ["password file for ASM are stored by default in an ASM disk group", "designated network is used for communication between ASM instances and their clients", "ASM clients can fail over to other ASM instances"],
    (78, 69): ["Single Client Access Name (SCAN) VIPs", "Grid Naming Service (GNS) VIP"],
    (78, 70): ["install RAC database software on a one-node cluster", "CLUVFY) may be used to check the cluster after installing", "multiple RAC Database 12c software homes"],
    (78, 71): ["CPUs have too large a run queue", "block is busy in the remote cache"],
    (78, 72): ["crsctl eval fail resource", "srvctl predict filesystem"],
    (78, 73): ["Stage the patch on the cluster node where the OPatch utility will be executed"],
    (78, 74): ["Ability to perform rolling patches", "Automatic failover for high availability", "Online conversion from RAC One Node databases to multi-instance RAC databases"],
    (78, 75): ["snapshot operations for all filesystems are serialized clusterwide", "same volume as their parent file system", "always point-in-time copies of the parent file system", "create a snapshot from an existing snapshot", "only be accessed when the file system is mounted"],
    (78, 76): ["uniformly managed across all instances in prod_pool", "srvctl stop service prevents logins to any instance of CDB1 using service HR"],
    (78, 78): ["balanced across all IP addresses defined for the SCAN", "failed over to another SCAN listener"],
    
    # ==================== 1z0-083 ====================
    (83, 1): ["querying DBA_ALERT_HISTORY", "space usage management alert is automatically cleared", "statistical counts for a specific unit"],
    (83, 4): ["privilege must be granted to the user performing the flashback", "Row Movement must be enabled"],
    (83, 5): ["four sections can be created serially", "four sections can be created in parallel"],
    (83, 6): ["filters in WHERE clauses", "re-optimize execution plans", "considers object statistics"],
    (83, 9): ["uses an auxiliary instance", "after a DDL operation has altered the table structure", "tables owed by the SYSTEM user"],
    (83, 12): ["PDB2 is not in UPGRADE state"],
    (83, 13): ["Single-byte character sets provide better performance", "Unicode enables information from any language to be stored"],
    (83, 14): ["backup sets or image copies", "can be consistent", "can be inconsistent"],
    (83, 16): ["DB_CACHE_SIZE for a PDB guarantees a minimum", "SHARED_POOL_SIZE for a PDB guarantees a minimum"],
    (83, 18): ["PDB snapshot can be a sparse copy", "DBCA) in silent mode", "PDB snapshot can be a full copy"],
    (83, 19): ["volume management, file system, and automatic restart", "CSS daemon runs from the Grid Infrastructure home"],
    (83, 23): ["poorly written SQL", "poorly trained users who do not commit transactions"],
    (83, 25): ["Oracle recovery files normally written to the FRA"],
    (83, 26): ["SPFILE can be recovered from memory", "orapwd utility", "lost index tablespace can be re-created without performing any recovery"],
    (83, 29): ["messages in the error stack are not errors", "channel ID where the failure occurred", "'Additional information' and a number"],
    (83, 30): ["containing the block being recovered remains online", "block being recovered is not accessible"],
    (83, 31): ["upgraded in a specific sequence", "target and source database are on the same platform"],
    (83, 32): ["Sorts and Hash Joins", "private SQL area (UGA) is located in the System Global Area (SGA) when using shared servers"],
    (83, 33): ["Control file backups can be created while connected to the root container", "BACKUP TABLESPACE"],
    (83, 34): ["STATISTICS_LEVEL is set to TYPICAL", "STATISTICS_LEVEL is set to ALL", "retained forever"],
    (83, 38): ["Virtual Private Catalog access to metadata", "base catalog must be enabled", "target PDB must be registered in a base catalog"],
    (83, 39): ["converting an application PDB to an application root", "converting an application seed to an application PDB", "converting a regular PDB to an application PDB"],
    (83, 41): ["SPFILE is included in the archival backup", "recovered to a consistent state", "ARCHIVAL attribute for a backup overrides"],
    (83, 44): ["creation of a local role is not allowed in CDB$ROOT"],
    (83, 45): ["eliminate estimation error"],
    (83, 46): ["Oracle Inventory group", "owns Oracle Restart and Oracle Automatic Storage Management binaries"],
    (83, 51): ["Binary compression adds CPU overhead", "only for locally managed tablespaces"],
    (83, 54): ["ADDM can run in a nonroot container", "AWR snapshots can be created in CDB$ROOT", "AWR reports can be generated while connected to any container", "AWR snapshots can be created in a PDB"],
    (83, 57): ["pull backup sets from the target database instance", "connection to an auxiliary instance is always required", "subset of the target database can be duplicated", "push copies to the auxiliary database instance"],
    (83, 59): ["FLASHBACK DATABASE"],
    (83, 62): ["can get backed up automatically as a binary copy", "can be backed up manually as a binary copy", "can be backed up manually as a trace file"],
    (83, 65): ["SQL statements to re-create the control file"],
    (83, 67): ["Oracle Virtual Private Database (VPD)", "grant access for an already registered database to a new virtual catalog owner"],
    (83, 76): ["transport data"],
    (83, 77): ["groups OSASM and OSDBA be assigned as secondary groups", "creates one disk group during installation", "includes both Oracle Restart and Oracle Automatic Storage Management"],
    (83, 80): ["image that can be distributed across multiple servers", "software-only Oracle Database installation and then running the roohctl -enable script"],
    (83, 81): ["CROSSCHECK BACKUP OF ARCHIVELOG ALL", "LIST EXPIRED"],
    (83, 82): ["Oracle Application Express configuration should be updated", "recovery catalog must be upgraded manually", "TNSNAMES.ORA entries must be updated"],
    (83, 83): ["each time the SPFILE is backed up manually", "whenever an RMAN backup is successfully recorded in the catalog", "whenever a new tablespace is created", "SPFILE) is automatically backed up each time the control file is backed up"],
    (83, 85): ["PDB snapshot can be a sparse copy", "PDB snapshot can be a full copy"],
    (83, 89): ["archivelog mode", "local UNDO mode"],
    (83, 93): ["only a common user with the required privilege can create an undo tablespace in CDB&ROOT", "automatically configured to use the default undo tablespace in CDB$ROOT", "each existing PDB has to be reopened for the new undo mode to take effect"],
    (83, 94): ["asynchronous disk I/O", "level of RMAN multiplexing"],
    (83, 99): ["orainstRoot.sh can be executed automatically", "root password cannot be specified in a response file"],
    (83, 100): ["Memory Advisor for the shared pool"],
    (83, 107): ["not in the current FRA", "Oracle recovery files in the current FRA that have not been backed up already"],
    (83, 109): ["when using synchronous I/O.", "noticeably less than an actual backup", "then read I/O is a likely bottleneck"],
    (83, 112): ["FLASHBACK DROP can undrop an index", "FLASHBACK DATABASE command, it is sometimes rolled forward using redo logs"],
    (83, 113): ["old version of the application installed after cloning completes", "up-to-date version of the application installed after cloning completes", "not required in an application container"],
    (83, 116): ["FLASHBACK drop requires that the RECYCLEBIN", "FLASHBACK version query requires undo"],
    (83, 117): ["CREATE_FILE_DEST clause to the statement", "Set only the PDB_FILE_NAME_CONVERT parameter", "Enable only OMF"],
    (83, 119): ["increase the Large Pool size by reducing the Shared Pool size", "increase the System Global Area size by reducing the Program Global Area size", "Decision Support Systems"],
    (83, 120): ["after losing all copies of the control file", "after losing an archived log from before the most recent backup", "after losing the SYSTEM tablespace"],
    (83, 124): ["deploy Oracle Database homes", "deploy Grid Infrastructure homes, including Oracle Restart", "Oracle Grid Infrastructure service"],
    (83, 128): ["empties the RECYCLE BIN", "prerequisite checks to verify if the Oracle database is ready for upgrade", "increases tablespace size, if required, to meet upgrade requirements"],
    (83, 130): ["oracle will be an owner of the Oracle Inventory", "oinstall, can be used for all Oracle software installations"],
    (83, 132): ["2, 4, 5"],
    (83, 133): ["snapshot copy PDB depends on a storage snapshot which can only be stored on specific file systems", "snapshot copy PDB can be created from a stand-alone clone PDB"],
    (83, 137): ["restored from backup files copied using O/S utilities", "added to the RMAN catalog as IMAGE COPIES", "NOARCHIVELOG mode using O/S utilities requires that the database instance be shut down"],
    (83, 138): ["exist in user-defined schemas only in application containers", "exist in CDB$ROOT and an application root"],
    (83, 139): ["PDB1 and PDB2 are in MOUNT state", "CDB$ROOT is in MOUNT state"],
    (83, 140): ["separate Oracle Grid Infrastructure home on the same server", "existing Oracle base can be used"],
    (83, 141): ["CURRENT online redo log group"],
    (83, 143): ["Index balanced B*Tree height is considered", "evaluating the cost of accessing a table using an index", "Statistics Advisor can help recommend"],
    (83, 145): ["Tablespaces are automatically created as needed while importing full exports", "convert conventional database users to local users", "convert common users to conventional users"],
    (83, 146): ["using SQL Developer", "using Oracle Data Pump", "CREATE TABLE AS SELECT SQL statement"],
    (83, 147): ["checkpoint process (CKPT)", "opens the database. SMON then rolls back any dead transactions"],
    (83, 148): ["ORCL database, the Oracle ASM instances, the +DATA and +FRA disk groups, and the LISTENER are started"],
    (83, 149): ["runs automatically after each AWR snapshot", "DBA can run it manually"],
    (83, 153): ["done on that physical standby database", "done on its primary database"],
    (83, 155): ["stored in a database keystore", "SET ENCRYPTION command overrides encryption settings specified by the CONFIGURE ENCRYPTION command"],
    (83, 156): ["done before installing Grid Infrastructure for a Standalone Server", "Oracle Preinstallation RPM can be used", "done after installing Grid Infrastructure for a Standalone Server"],
    (83, 157): ["can be created in a pluggable database", "always possible for RMAN to connect to a pluggable database as a target.", "non-container database"],
    (83, 158): ["Schema Only accounts can be granted administrator privileges", "Privilege Analysis is included in Oracle Enterprise Edition and no longer requires Database Vault", "audit only events that are issued directly by an audited user"],
    (83, 159): ["self-contained archive backup are not considered obsolete for two years", "SPFILE is included in the self-contained archival backup", "control file is included in the self-contained archival backup"],
    (83, 160): ["Stateless alerts can be purged manually", "Stateless alerts can be cleared manually", "Stateful alerts are purged automatically"],
    (83, 161): ["database is in ARCHIVELOG mode", "Backups can be done incrementally"],
    (83, 162): ["backup piece can belong to only one backup set", "different backup pieces in the same backup set", "multiple data files can be contained in one backup piece", "multiple data files can be contained in one backup set"],
    (83, 163): ["BACKUP DATABASE command will create a pluggable database", "BACKUP PLUGGABLE DATABASE command can be used to back up CDB$ROOT"],
    (83, 164): ["pluggable database in silent mode", "cloning a remote container database in silent mode"],
    (83, 165): ["lack of a clean restore point"],
    (83, 167): ["used for both Oracle Database and Oracle Grid Infrastructure installation", "install and upgrade Oracle Database for single-instance and cluster configurations"],
    (83, 168): ["RMAN CONFIGURE command to specify duplexing", "can be written to media."],
    (83, 169): ["SQL statements"],
    (83, 170): ["leave a plugged-in tablespace in read-only mode", "leave a plugged-in tablespace in read/write mode", "Simultaneous data pump jobs can be limited"],
    (83, 172): ["installer will prompt for the root or sudo password", "specify the path of the sudo program"],
    (83, 173): ["KEEP FOREVER clause with the BACKUP command", "RMAN stored scripts", "REPORT SCHEMA command to list a database's data files and tablespaces at times in the past"],
    (83, 175): ["HR_ROOT replica must exist in the remote CDB", "proxy PDB must exist in the application root in the local CDB"],
    (83, 176): ["best optimizes one SQL statement can degrade the performance of others", "tuned automatically by the Oracle server"],
    (83, 177): ["applications and middleware", "both Oracle Database and Oracle Grid Infrastructure, including Oracle Restart"],
    (83, 180): ["mounting disk groups", "managing Allocation Units (AUs)", "managing space allocation for Oracle ASM files"],
    (83, 181): ["seven"]
}

def clean_text(t):
    return re.sub(r'\s+', ' ', str(t or '')).strip()

def normalize_text(text):
    t = re.sub(r'[,;:?!\'\"()\[\]]|\.(?=\s|$)', ' ', text or '')
    return re.sub(r'\s+', ' ', t).strip()

def is_token_in_text(token, text):
    t = token.strip()
    if t.endswith('.'):
        pattern = r'(?<![A-Za-z0-9_\$\.])' + re.escape(t[:-1]) + r'\.(?:\s|$)'
        return bool(re.search(pattern, text, re.IGNORECASE))
        
    norm_text = normalize_text(text)
    norm_token = normalize_text(t)
    pattern = r'(?<![A-Za-z0-9_\$\.])' + re.escape(norm_token) + r'(?![A-Za-z0-9_\$\.])'
    return bool(re.search(pattern, norm_text, re.IGNORECASE))

def extract_candidates(text):
    candidates = []
    norm = normalize_text(text)
    tokens = [tok for tok in norm.split(' ') if tok]
    
    # 1. Single words (1-grams): MUST be technical
    for tok in tokens:
        if is_technical_single_word(tok):
            candidates.append((1, tok))
            
    # 2. Number lists like "2, 4, 5"
    for nm in re.findall(r'\b\d+(?:,\s*\d+)+\b', text):
        candidates.append((1, nm))
        
    # 3. Multi-word phrases (2-grams to 6-grams)
    words = text.split()
    for n in range(2, min(7, len(words) + 1)):
        for i in range(len(words) - n + 1):
            slice_words = words[i:i+n]
            phrase = " ".join(slice_words).strip('.,;:')
            
            # Avoid fake article prefixes like "the OCR" or "a PDB"
            if re.match(r'^(the|a|an)\s+[A-Za-z0-9_\$]+$', phrase, re.I):
                continue
                
            # Score bonus if has an action verb
            has_verb = any(w.lower().rstrip('.,;:') in ACTION_VERBS for w in slice_words)
            candidates.append((n, phrase, has_verb))
            
    return candidates

def find_minimal_cover_for_question(q, exam_num=78):
    qid = q['id']
    if (exam_num, qid) in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[(exam_num, qid)]
        
    correct_keys = set(q.get('correct', []))
    correct_opts = [o for o in q.get('options', []) if (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    all_needed_keys = set(o.get('letter') or o.get('key') for o in correct_opts)
    
    cand_coverage = {}
    cand_info = {}
    
    all_cands = extract_candidates(" ".join(o['text'] for o in correct_opts))
    for opt in correct_opts:
        all_cands.extend(extract_candidates(opt['text']))
        
    seen = set()
    unique_cands = []
    for item in all_cands:
        n = item[0]
        cand = item[1]
        has_verb = item[2] if len(item) > 2 else False
        cl = cand.lower().strip()
        if cl not in seen:
            seen.add(cl)
            unique_cands.append((n, cand.strip(), has_verb))
            
    for n, cand, has_verb in unique_cands:
        in_wrong = any(is_token_in_text(cand, wo['text']) for wo in wrong_opts)
        if in_wrong:
            continue
            
        covered = set()
        for opt in correct_opts:
            okey = opt.get('letter') or opt.get('key')
            if is_token_in_text(cand, opt['text']):
                covered.add(okey)
                
        if covered:
            score = 0
            if is_technical_single_word(cand):
                score += 80
            if '_' in cand or '$' in cand: score += 50
            if cand.isupper() and len(cand) >= 3: score += 40
            if has_verb: score += 40 # Strong preference for action verbs + nouns
            if 3 <= len(cand.split()) <= 5: score += 30 # Sweet spot for meaningful phrases
            
            score += len(covered) * 120
            
            cand_coverage[cand] = covered
            cand_info[cand] = (n, -score, len(cand), cand)
            
    all_valid_cands = sorted(cand_coverage.keys(), key=lambda c: (cand_info[c][1], cand_info[c][0], cand_info[c][2]))
    
    best_solution = None
    for r in range(1, len(all_needed_keys) + 1):
        for combo in itertools.combinations(all_valid_cands, r):
            union_covered = set().union(*(cand_coverage[c] for c in combo))
            if all_needed_keys.issubset(union_covered):
                best_solution = list(combo)
                break
        if best_solution:
            break
            
    return best_solution or []

def extract_anchor_for_question(q):
    exp = q.get('explanation', '')
    if not exp:
        return ""
    
    exp_text = re.sub(r'```[\s\S]*?```', '', exp)
    sentences = re.split(r'(?<=[.!?])\s+', exp_text)
    
    candidate_anchors = []
    for s in sentences:
        s_clean = clean_text(s)
        s_clean = re.sub(r'^(The (?:defensible )?key is [A-G](?:, [A-G])*(?: and [A-G])*\.?\s*)', '', s_clean, flags=re.I)
        s_clean = re.sub(r'^(Option [A-G] is (?:the )?correct(?: answer)?(?::| because|\.)?\s*)', '', s_clean, flags=re.I)
        s_clean = re.sub(r'^([A-G] is correct(?::| because|\.)?\s*)', '', s_clean, flags=re.I)
        s_clean = re.sub(r'^(Options [A-G](?:, [A-G])*(?: and [A-G])* are correct(?::| because|\.)?\s*)', '', s_clean, flags=re.I)
        s_clean = clean_text(s_clean)
        
        if re.match(r'^(Option [A-G] is (?:false|incorrect)|[A-G] is false)', s_clean, re.I):
            continue
        if re.search(r'\b(is false because|is incorrect because)\b', s_clean, re.I):
            continue
        if 'For a practical investigation' in s_clean or 'After extending a tablespace' in s_clean:
            continue
            
        if 35 <= len(s_clean) <= 160:
            candidate_anchors.append(s_clean)
            
    if candidate_anchors:
        return candidate_anchors[0]
        
    for s in sentences:
        sc = clean_text(s)
        if len(sc) > 30:
            return sc[:140] + ("..." if len(sc) > 140 else "")
            
    return "Review the core Oracle documentation principles for this topic."

def process_exam_file(filepath, exam_num, dry_run=False):
    print(f"\nProcessing {filepath} (Exam {exam_num})...")
    with open(filepath, 'r', encoding='utf-8') as f:
        questions = json.load(f)
        
    updated = 0
    errors = 0
    for q in questions:
        kws = find_minimal_cover_for_question(q, exam_num)
        if not kws:
            print(f"ERROR: Q#{q['id']} could not find minimal exclusive cover!")
            errors += 1
            continue
            
        # 1. Verify no standalone articles or fake article pairs or isolated generic words
        for kw in kws:
            if re.match(r'^(the|a|an)\s+[A-Za-z0-9_\$]+$', kw, re.I):
                print(f"ERROR: Q#{q['id']} kw '{kw}' is an article-noun pair!")
                errors += 1
            if kw.lower() in COMMON_ORACLE_GENERIC_WORDS and not is_technical_single_word(kw):
                print(f"ERROR: Q#{q['id']} kw '{kw}' is an isolated generic word!")
                errors += 1
                
        # 2. Verify exclusivity
        correct_keys = set(q.get('correct', []))
        wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
        for kw in kws:
            for wo in wrong_opts:
                wo_clean = wo['text'].strip()
                if re.match(r'^[\d,\s]+$', wo_clean):
                    if kw.strip() == wo_clean:
                        print(f"ERROR: Q#{q['id']} kw '{kw}' matches wrong numeric option {wo['key']}!")
                        errors += 1
                elif is_token_in_text(kw, wo['text']):
                    # Permitted user exception for Q29 (shared conceptual benefit block pings)
                    if q['id'] == 29 and exam_num == 78 and kw == 'block pings':
                        continue
                    print(f"ERROR: Q#{q['id']} kw '{kw}' found in wrong option {wo['key']}!")
                    errors += 1
                    
        # 3. Verify coverage
        correct_opts = [o for o in q.get('options', []) if (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
        all_needed_keys = set(o.get('letter') or o.get('key') for o in correct_opts)
        covered = set()
        for kw in kws:
            for co in correct_opts:
                ckey = co.get('letter') or co.get('key')
                if is_token_in_text(kw, co['text']):
                    covered.add(ckey)
        if not all_needed_keys.issubset(covered):
            print(f"ERROR: Q#{q['id']} kws {kws} do not cover all correct options ({all_needed_keys - covered} missing)!")
            errors += 1
            
        anchor = extract_anchor_for_question(q)
        q['mnemonic'] = {
            'keywords': kws,
            'anchor': anchor
        }
        updated += 1
        
    print(f"Enriched {updated}/{len(questions)} questions with exclusive minimal mnemonics (Errors: {errors}).")
    
    if not dry_run and errors == 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"Successfully saved {filepath}")
    elif dry_run:
        print("[Dry Run] Did not write to disk.")
    else:
        print("Encountered errors, aborting save.")
        raise RuntimeError(f"Failed to process {filepath} due to {errors} errors.")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    process_exam_file(os.path.join(data_dir, '1z0-078.json'), 78, dry_run=False)
    process_exam_file(os.path.join(data_dir, '1z0-083.json'), 83, dry_run=False)
