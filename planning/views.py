import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import math

from .models import (
    Currency, OBS, Curve, UDFType, UnitOfMeasurement, Project, Calendar,
    SchedulingOption, WBS, Resource, ActivityType, ResourceRate, Task,
    ActivityCode, TaskResource, TaskActivity, UDFValue
)

# Set up logging
logging.basicConfig(
    filename='import_skipped_rows.log',  # Log file name
    level=logging.INFO,  # Log level to INFO to capture both warnings and errors
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
)

def clean_value(value):
    """Convert invalid, NaN, or HTML-contaminated values to None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "" or stripped.lower().startswith("<html"):
            return None
        try:
            if stripped.isdigit():
                return int(stripped)
            return float(stripped)
        except Exception:
            return None
    return value

def safe_bulk_create(model, objects, unique_field):
    """Safely bulk_create without duplicate key conflicts."""
    # Fetch existing ids from the database
    existing_ids = set(model.objects.values_list(unique_field, flat=True))
    new_objects = []

    # Check each object and skip if it already exists
    for obj in objects:
        # Check if object has a unique identifier already in the database
        if getattr(obj, unique_field) not in existing_ids:
            new_objects.append(obj)
        else:
            logging.warning(f"⚠️ Skipped duplicate {model.__name__} row with {unique_field}={getattr(obj, unique_field)}")

    # Bulk insert the valid objects
    if new_objects:
        model.objects.bulk_create(new_objects)
        logging.info(f"{model.__name__}: inserted {len(new_objects)} records, skipped {len(objects) - len(new_objects)} duplicates.")
    else:
        logging.info(f"{model.__name__}: No new records to insert, all rows were duplicates.")

@csrf_exempt
def import_all_data(request):
    if request.method != 'POST' or 'excel_file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'No file uploaded or incorrect request method.'})

    excel_file = request.FILES['excel_file']
    fs = FileSystemStorage()
    filename = fs.save(excel_file.name, excel_file)
    file_path = fs.path(filename)

    try:
        sheet_names = [
            'CURRTYPE', 'OBS', 'RSRCCURVDATA', 'UDFTYPE', 'UMEASURE', 'PROJECT',
            'CALENDAR', 'SCHEDOPTIONS', 'PROJWBS', 'RSRC', 'ACTVTYPE', 'RSRCRATE',
            'TASK', 'ACTVCODE', 'TASKRSRC', 'TASKACTV', 'UDFVALUE'
        ]
        sheets = {
            name: pd.read_excel(file_path, sheet_name=name).where(
                pd.notnull(pd.read_excel(file_path, sheet_name=name)), None
            )
            for name in sheet_names
        }
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error reading Excel: {str(e)}'})

    # ================== CURRENCY ==================
    df_currency = sheets['CURRTYPE']
    currency_data = []
    for _, row in df_currency.iterrows():
        try:
            currency_data.append(Currency(
                curr_id=row['curr_id'],
                decimal_digit_cnt=clean_value(row['decimal_digit_cnt']),
                curr_symbol=row['curr_symbol'],
                decimal_symbol=row['decimal_symbol'],
                digit_group_symbol=row['digit_group_symbol'],
                pos_curr_fmt_type=row.get('pos_curr_fmt_type', ''),
                neg_curr_fmt_type=row.get('neg_curr_fmt_type', ''),
                curr_type=row['curr_type'],
                curr_short_name=row['curr_short_name'],
                group_digit_cnt=clean_value(row['group_digit_cnt']),
                base_exch_rate=clean_value(row.get('base_exch_rate', None))
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped CURRENCY row due to error: {e}")
    safe_bulk_create(Currency, currency_data, "curr_id")

    # ================== OBS ==================
    df_obs = sheets['OBS']
    obs_data = []
    obs_rows = []

    for _, row in df_obs.iterrows():
        seq = clean_value(row.get('seq_num'))
        if seq is None:
            logging.warning(f"⚠️ Skipped OBS with missing seq_num (obs_id={row.get('obs_id')})")
            continue
        obs_rows.append(row)

    # Sort OBS: records with parent_obs_id=None first, then by parent_obs_id
    # This ensures parents are created before children
    obs_rows_sorted = sorted(obs_rows, key=lambda r: (
        0 if pd.isna(r.get('parent_obs_id')) or r.get('parent_obs_id') is None else 1,
        str(r.get('parent_obs_id', ''))
    ))

    for row in obs_rows_sorted:
        try:
            obs_data.append(OBS(
                obs_id=row['obs_id'],
                parent_obs_id=clean_value(row.get('parent_obs_id', None)),
                guid=row.get('guid', ''),
                seq_num=clean_value(row.get('seq_num'))
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped OBS row due to: {e}")

    safe_bulk_create(OBS, obs_data, "obs_id")

    # ================== CURVE ==================
    df_curve = sheets['RSRCCURVDATA']
    curve_data = []
    for _, row in df_curve.iterrows():
        try:
            curve_data.append(Curve(
                curv_id=row['curv_id'],
                curv_name=row['curv_name'],
                default_flag=row['default_flag'],
                **{f"pct_usage_{i}": clean_value(row.get(f"pct_usage_{i}", None)) for i in range(21)}
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped CURVE row: {e}")
    safe_bulk_create(Curve, curve_data, "curv_id")

    # ================== UDFTYPE ==================
    df_udftype = sheets['UDFTYPE']
    udf_type_data = []
    for _, row in df_udftype.iterrows():
        try:
            udf_type_data.append(UDFType(
                udf_type_id=row['udf_type_id'],
                table_name=row['table_name'],
                udf_type_name=row['udf_type_name'],
                udf_type_label=row['udf_type_label'],
                logical_data_type=row['logical_data_type'],
                super_flag=row['super_flag']
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped UDFTYPE row: {e}")
    safe_bulk_create(UDFType, udf_type_data, "udf_type_id")

    # ================== UNIT OF MEASUREMENT ==================
    df_uom = sheets['UMEASURE']
    uom_data = []
    for _, row in df_uom.iterrows():
        seq = clean_value(row.get('seq_num'))
        if seq is None:
            logging.warning(f"⚠️ Skipped UOM with missing seq_num (unit_id={row.get('unit_id')})")
            continue
        try:
            uom_data.append(UnitOfMeasurement(
                unit_id=row['unit_id'],
                seq_num=seq,
                unit_abbrev=row['unit_abbrev'],
                unit_name=row['unit_name']
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped UOM row due to: {e}")
    safe_bulk_create(UnitOfMeasurement, uom_data, "unit_id")

    # ================== PROJECT ==================
    df_project = sheets['PROJECT']
    project_data = []
    for _, row in df_project.iterrows():
        try:
            project_data.append(Project(
                proj_id=row['proj_id'],
                fy_start_month_num=clean_value(row['fy_start_month_num']),
                rsrc_self_add_flag=row['rsrc_self_add_flag'],
                allow_complete_flag=row['allow_complete_flag'],
                rsrc_multi_assign_flag=row['rsrc_multi_assign_flag'],
                checkout_flag=row['checkout_flag'],
                project_flag=row['project_flag'],
                step_complete_flag=row['step_complete_flag'],
                cost_qty_recalc_flag=row['cost_qty_recalc_flag'],
                batch_sum_flag=row['batch_sum_flag'],
                guid=row.get('guid', ''),
                def_qty_type=row['def_qty_type'],
                def_rate_type=row['def_rate_type'],
                def_task_type=row['def_task_type'],
                act_pct_link_flag=row['act_pct_link_flag']
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped PROJECT row due to: {e}")
    safe_bulk_create(Project, project_data, "proj_id")

    # ================== CALENDAR ==================
    df_calendar = sheets['CALENDAR']
    calendar_data = []
    for _, row in df_calendar.iterrows():
        clndr_id = clean_value(row.get('clndr_id'))
        if not clndr_id:
            logging.warning("⚠️ Skipped CALENDAR missing clndr_id")
            continue

        proj_val = row.get('proj_id')
        project = None

        # ✅ Validate and resolve project safely
        if isinstance(proj_val, (int, float)):
            project = Project.objects.filter(proj_id=int(proj_val)).first()
        else:
            # Excel often auto-parses IDs as datetime or text
            logging.warning(f"⚠️ Skipped CALENDAR invalid proj_id='{proj_val}' (must be numeric)")
            continue

        if not project:
            logging.warning(f"⚠️ Skipped CALENDAR missing project reference proj_id={proj_val}")
            continue

        try:
            calendar_data.append(Calendar(
                clndr_id=clndr_id,
                default_flag=row.get('default_flag', ''),
                clndr_name=row.get('clndr_name', ''),
                proj_id=project,
                base_clndr_id=clean_value(row.get('base_clndr_id')),
                last_chng_date=row.get('last_chng_date') if not isinstance(row.get('last_chng_date'), str) else None,
                clndr_type=row.get('clndr_type', ''),
                day_hr_cnt=clean_value(row.get('day_hr_cnt')),
                week_hr_cnt=clean_value(row.get('week_hr_cnt')),
                month_hr_cnt=clean_value(row.get('month_hr_cnt')),
                year_hr_cnt=clean_value(row.get('year_hr_cnt')),
                rsrc_private=row.get('rsrc_private', '')
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped CALENDAR (clndr_id={clndr_id}) due to: {e}")

    safe_bulk_create(Calendar, calendar_data, "clndr_id")

    # ================== SCHEDULING OPTIONS ==================
    df_schedoptions = sheets['SCHEDOPTIONS']
    schedoptions_data = []
    for _, row in df_schedoptions.iterrows():
        try:
            schedoptions_data.append(SchedulingOption(
                schedoptions_id=row['schedoptions_id'],
                proj_id=Project.objects.get(proj_id=row['proj_id']),
                sched_outer_depend_type=row['sched_outer_depend_type'],
                sched_open_critical_flag=row['sched_open_critical_flag'],
                sched_lag_early_start_flag=row['sched_lag_early_start_flag'],
                sched_retained_logic=row['sched_retained_logic'],
                sched_setplantoforecast=row['sched_setplantoforecast'],
                sched_float_type=row['sched_float_type'],
                sched_calendar_on_relationship_lag=row['sched_calendar_on_relationship_lag'],
                sched_use_expect_end_flag=row['sched_use_expect_end_flag'],
                level_within_float_flag=row['level_within_float_flag'],
                level_keep_sched_date_flag=row['level_keep_sched_date_flag'],
                level_all_rsrc_flag=row['level_all_rsrc_flag'],
                sched_use_project_end_date_for_float=row['sched_use_project_end_date_for_float'],
                enable_multiple_longest_path_calc=row['enable_multiple_longest_path_calc'],
                limit_multiple_longest_path_calc=row['limit_multiple_longest_path_calc'],
                max_multiple_longest_path=clean_value(row['max_multiple_longest_path']),
                use_total_float_multiple_longest_paths=row['use_total_float_multiple_longest_paths'],
                key_activity_for_multiple_longest_paths=row['key_activity_for_multiple_longest_paths'],
                LevelPriorityList=row.get('LevelPriorityList', '')
            ))
        except Project.DoesNotExist:
            logging.warning(f"⚠️ Skipped SCHEDOPTION due to missing Project ID {row.get('proj_id')}")
        except Exception as e:
            logging.warning(f"⚠️ Skipped SCHEDOPTION row due to: {e}")
    safe_bulk_create(SchedulingOption, schedoptions_data, "schedoptions_id")

    # ================== WBS ==================
    df_wbs = sheets['PROJWBS']
    wbs_data = []
    for _, row in df_wbs.iterrows():
        seq = clean_value(row.get('seq_num'))
        if seq is None:
            logging.warning(f"⚠️ Skipped WBS (wbs_id={row.get('wbs_id')}) due to missing seq_num")
            continue
        try:
            wbs_data.append(WBS(
                wbs_id=row['wbs_id'],
                proj_id=Project.objects.get(proj_id=row['proj_id']),
                obs_id=OBS.objects.get(obs_id=row['obs_id']),
                seq_num=seq,
                est_wt=clean_value(row['est_wt']),
                proj_node_flag=row['proj_node_flag'],
                sum_data_flag=row['sum_data_flag'],
                status_code=row['status_code'],
                wbs_short_name=row['wbs_short_name'],
                wbs_name=row['wbs_name'],
                phase_id=row['phase_id'],
                parent_wbs_id=clean_value(row.get('parent_wbs_id', None)),
                ev_user_pct=clean_value(row['ev_user_pct']),
                ev_etc_user_value=clean_value(row['ev_etc_user_value']),
                orig_cost=clean_value(row['orig_cost']),
                independ_remain_total_cost=clean_value(row['independ_remain_total_cost']),
                ann_dscnt_rate_pct=clean_value(row['ann_dscnt_rate_pct']),
                dscnt_period_type=row['dscnt_period_type'],
                independ_remain_work_qty=clean_value(row.get('independ_remain_work_qty', None))
            ))
        except (Project.DoesNotExist, OBS.DoesNotExist):
            logging.warning(f"⚠️ Skipped WBS (wbs_id={row.get('wbs_id')}) missing project/OBS")
        except Exception as e:
            logging.warning(f"⚠️ Skipped WBS (wbs_id={row.get('wbs_id')}) due to: {e}")
    safe_bulk_create(WBS, wbs_data, "wbs_id")


    # ================== RESOURCE ==================
    df_resource = sheets['RSRC']
    resource_data = []
    for _, row in df_resource.iterrows():
        try:
            calendar = Calendar.objects.filter(clndr_id=row.get('clndr_id')).first()
            obs = OBS.objects.filter(obs_id=row.get('pobs_id')).first()
            if not calendar or not obs:
                logging.warning(f"⚠️ Skipped RESOURCE due to missing calendar or OBS (rsrc_id={row.get('rsrc_id')})")
                continue
            resource_data.append(Resource(
                rsrc_id=row['rsrc_id'],
                parent_rsrc_id=clean_value(row.get('parent_rsrc_id', None)),
                clndr_id=calendar,
                role_id=row.get('role_id', ''),
                shift_id=row.get('shift_id', ''),
                user_id=row.get('user_id', ''),
                pobs_id=obs,
                guid=row.get('guid', ''),
                rsrc_seq_num=clean_value(row.get('rsrc_seq_num', None)),
                email_addr=row.get('email_addr', ''),
                employee_code=row.get('employee_code', ''),
                office_phone=row.get('office_phone', ''),
                other_phone=row.get('other_phone', ''),
                rsrc_name=row['rsrc_name'],
                rsrc_short_name=row['rsrc_short_name'],
                rsrc_title_name=row.get('rsrc_title_name', ''),
                def_qty_per_hr=clean_value(row.get('def_qty_per_hr', None)),
                cost_qty_type=row.get('cost_qty_type', '')
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped RESOURCE (rsrc_id={row.get('rsrc_id')}) due to: {e}")
    safe_bulk_create(Resource, resource_data, "rsrc_id")

    # ================== ACTIVITY TYPE ==================
    df_actvtype = sheets['ACTVTYPE']
    actvtype_data = []
    for _, row in df_actvtype.iterrows():
        seq = clean_value(row.get('seq_num'))
        if seq is None:
            logging.warning(f"⚠️ Skipped ACTVTYPE (id={row.get('actv_code_type_id')}) due to missing seq_num")
            continue

        project = Project.objects.filter(proj_id=row.get('proj_id')).first()
        if not project:
            logging.warning(f"⚠️ Skipped ACTVTYPE (id={row.get('actv_code_type_id')}) missing valid project reference")
            continue

        wbs_id_val = clean_value(row.get('wbs_id'))
        if not wbs_id_val:
            logging.warning(f"⚠️ Skipped ACTVTYPE (id={row.get('actv_code_type_id')}) missing wbs_id")
            continue

        wbs = WBS.objects.filter(wbs_id=wbs_id_val).first()
        if not wbs:
            logging.warning(f"⚠️ Skipped ACTVTYPE (id={row.get('actv_code_type_id')}) invalid WBS reference (wbs_id={wbs_id_val})")
            continue

        try:
            actvtype_data.append(ActivityType(
                actv_code_type_id=row['actv_code_type_id'],
                actv_short_len=clean_value(row['actv_short_len']),
                seq_num=seq,
                actv_code_type=row['actv_code_type'],
                proj_id=project,
                wbs_id=wbs
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped ACTVTYPE row (actv_code_type_id={row.get('actv_code_type_id')}) due to: {e}")

    safe_bulk_create(ActivityType, actvtype_data, "actv_code_type_id")

    # ================== RESOURCE RATE ==================
    df_rsrcrate = sheets['RSRCRATE']
    rsrcrate_data = []
    for _, row in df_rsrcrate.iterrows():
        resource = Resource.objects.filter(rsrc_id=row.get('rsrc_id')).first()
        if not resource:
            logging.warning(f"⚠️ Skipped RSRCRATE missing resource (id={row.get('rsrc_id')})")
            continue
        try:
            rsrcrate_data.append(ResourceRate(
                rsrc_rate_id=row['rsrc_rate_id'],
                rsrc_id=resource,
                max_qty_per_hr=clean_value(row.get('max_qty_per_hr')),
                cost_per_qty=clean_value(row.get('cost_per_qty')),
                start_date=row.get('start_date'),
                shift_period_id=clean_value(row.get('shift_period_id')),
                cost_per_qty2=clean_value(row.get('cost_per_qty2')),
                cost_per_qty3=clean_value(row.get('cost_per_qty3')),
                cost_per_qty4=clean_value(row.get('cost_per_qty4'))
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped RSRCRATE row due to: {e}")
    safe_bulk_create(ResourceRate, rsrcrate_data, "rsrc_rate_id")

    # ================== TASK ==================
    df_task = sheets['TASK']
    task_data = []
    for _, row in df_task.iterrows():
        proj = Project.objects.filter(proj_id=row.get('proj_id')).first()
        wbs = WBS.objects.filter(wbs_id=row.get('wbs_id')).first()
        cal = Calendar.objects.filter(clndr_id=row.get('clndr_id')).first()
        if not proj or not wbs or not cal:
            logging.warning(f"⚠️ Skipped TASK missing foreign key(s) task_id={row.get('task_id')}")
            continue
        try:
            task_data.append(Task(
                task_id=row['task_id'],
                proj_id=proj,
                wbs_id=wbs,
                clndr_id=cal,
                phys_complete_pct=clean_value(row.get('phys_complete_pct')),
                rev_fdbk_flag=row.get('rev_fdbk_flag', ''),
                est_wt=clean_value(row.get('est_wt')),
                lock_plan_flag=row.get('lock_plan_flag', ''),
                auto_compute_act_flag=row.get('auto_compute_act_flag', ''),
                complete_pct_type=row.get('complete_pct_type', ''),
                target_start_date=row.get('target_start_date'),
                target_end_date=row.get('target_end_date'),
                rem_late_start_date=row.get('rem_late_start_date'),
                rem_late_end_date=row.get('rem_late_end_date'),
                cstr_type=row.get('cstr_type', ''),
                priority_type=row.get('priority_type', ''),
                suspend_date=row.get('suspend_date'),
                resume_date=row.get('resume_date'),
                float_path=clean_value(row.get('float_path')),
                float_path_order=clean_value(row.get('float_path_order'))
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped TASK task_id={row.get('task_id')} due to: {e}")
    safe_bulk_create(Task, task_data, "task_id")

    # ================== ACTIVITY CODE ==================
    df_actvcode = sheets['ACTVCODE']
    actvcode_data = []
    for _, row in df_actvcode.iterrows():
        # Validate actv_code_type_id to ensure it's numeric
        actv_type_val = row.get('actv_code_type_id')
        if not isinstance(actv_type_val, (int, float)):
            logging.warning(f"⚠️ Skipped ACTVCODE invalid actv_code_type_id='{actv_type_val}' (must be numeric)")
            continue
        
        actv_type = ActivityType.objects.filter(actv_code_type_id=int(actv_type_val)).first()
        if not actv_type:
            logging.warning(f"⚠️ Skipped ACTVCODE missing actv_type {actv_type_val}")
            continue
        
        try:
            actvcode_data.append(ActivityCode(
                actv_code_id=row['actv_code_id'],
                parent_actv_code_id=clean_value(row.get('parent_actv_code_id')),
                actv_code_type_id=actv_type,
                actv_code_name=row['actv_code_name'],
                short_name=row.get('short_name', ''),
                seq_num=clean_value(row.get('seq_num')),
                color=row.get('color', ''),
                total_assignments=clean_value(row.get('total_assignments'))
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped ACTVCODE row (actv_code_id={row.get('actv_code_id')}) due to: {e}")

    safe_bulk_create(ActivityCode, actvcode_data, "actv_code_id")
    # ================== TASK RESOURCE ==================
    df_taskrsrc = sheets['TASKRSRC']
    taskrsrc_data = []
    for _, row in df_taskrsrc.iterrows():
        proj = Project.objects.filter(proj_id=row.get('proj_id')).first()
        task = Task.objects.filter(task_id=row.get('task_id')).first()
        res = Resource.objects.filter(rsrc_id=row.get('rsrc_id')).first()
        obs = OBS.objects.filter(obs_id=row.get('pobs_id')).first()
        if not (proj and task and res and obs):
            logging.warning(f"⚠️ Skipped TASKRSRC missing relation taskrsrc_id={row.get('taskrsrc_id')}")
            continue
        try:
            taskrsrc_data.append(TaskResource(
                taskrsrc_id=row['taskrsrc_id'],
                task_id=task,
                proj_id=proj,
                cost_qty_link_flag=row.get('cost_qty_link_flag', ''),
                role_id=row.get('role_id', ''),
                acct_id=clean_value(row.get('acct_id')),
                rsrc_id=res,
                pobs_id=obs,
                skill_level=clean_value(row.get('skill_level')),
                remain_qty=clean_value(row.get('remain_qty')),
                restart_date=row.get('restart_date'),
                target_start_date=row.get('target_start_date'),
                target_end_date=row.get('target_end_date'),
                rem_late_start_date=row.get('rem_late_start_date'),
                rem_late_end_date=row.get('rem_late_end_date'),
                rollup_dates_flag=row.get('rollup_dates_flag', ''),
                remain_crv=row.get('remain_crv', ''),
                actual_crv=clean_value(row.get('actual_crv'))
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped TASKRSRC row due to: {e}")
    safe_bulk_create(TaskResource, taskrsrc_data, "taskrsrc_id")

    # ================== TASK ACTIVITY ==================
    df_taskactv = sheets['TASKACTV']
    taskactv_data = []
    for _, row in df_taskactv.iterrows():
        # Validate actv_code_type_id to ensure it's numeric
        actv_type_val = row.get('actv_code_type_id')
        if not isinstance(actv_type_val, (int, float)):  # Check if it is not numeric
            logging.warning(f"⚠️ Skipped TASKACTV invalid actv_code_type_id='{actv_type_val}' (must be numeric)")
            continue  # Skip this row if the value is invalid

        actv_code_val = row.get('actv_code_id')
        if not isinstance(actv_code_val, (int, float)):  # Check if it is not numeric
            logging.warning(f"⚠️ Skipped TASKACTV invalid actv_code_id='{actv_code_val}' (must be numeric)")
            continue  # Skip this row if the value is invalid

        proj_val = row.get('proj_id')
        if not isinstance(proj_val, (int, float)):  # Check if it is not numeric
            logging.warning(f"⚠️ Skipped TASKACTV invalid proj_id='{proj_val}' (must be numeric)")
            continue  # Skip this row if the value is invalid

        task_val = row.get('task_id')
        if not isinstance(task_val, (int, float)):  # Check if it is not numeric
            logging.warning(f"⚠️ Skipped TASKACTV invalid task_id='{task_val}' (must be numeric)")
            continue  # Skip this row if the value is invalid

        # Proceed with filtering if values are valid
        task = Task.objects.filter(task_id=int(task_val)).first()
        actv_type = ActivityType.objects.filter(actv_code_type_id=int(actv_type_val)).first()
        actv_code = ActivityCode.objects.filter(actv_code_id=int(actv_code_val)).first()
        proj = Project.objects.filter(proj_id=int(proj_val)).first()

        if not (task and actv_type and actv_code and proj):
            logging.warning(f"⚠️ Skipped TASKACTV missing relation(s): task={task_val}, actv_type={actv_type_val}, actv_code={actv_code_val}, proj={proj_val}")
            continue

        try:
            taskactv_data.append(TaskActivity(
                task_id=task,
                actv_code_type_id=actv_type,
                actv_code_id=actv_code,
                proj_id=proj
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped TASKACTV row due to: {e}")

    # Bulk create the valid TaskActivity entries
    safe_bulk_create(TaskActivity, taskactv_data, "id")


    # ================== UDF VALUE ==================
    df_udfvalue = sheets['UDFVALUE']
    udfvalue_data = []
    for _, row in df_udfvalue.iterrows():
        udf_type = UDFType.objects.filter(udf_type_id=row.get('udf_type_id')).first()
        proj = Project.objects.filter(proj_id=row.get('proj_id')).first()
        if not (udf_type and proj):
            logging.warning(f"⚠️ Skipped UDFVALUE missing udf_type/project fk_id={row.get('fk_id')}")
            continue
        
        # Validate and clean udf_date
        udf_date_val = row.get('udf_date')
        valid_date = None
        
        if udf_date_val is not None:
            # Check if it's a valid datetime object (pandas Timestamp)
            if isinstance(udf_date_val, pd.Timestamp):
                valid_date = udf_date_val
            # Check if it's a string that's not just "0" or empty
            elif isinstance(udf_date_val, str) and udf_date_val.strip() not in ['', '0']:
                try:
                    valid_date = pd.to_datetime(udf_date_val)
                except Exception as e:
                    logging.warning(f"⚠️ Invalid date format for UDFVALUE fk_id={row.get('fk_id')}: '{udf_date_val}', Error: {e}")
            # If it's already a datetime.datetime object
            elif hasattr(udf_date_val, 'year'):
                valid_date = udf_date_val
        
        if valid_date is None:
            logging.warning(f"⚠️ Skipped UDFVALUE with invalid or missing date for fk_id={row.get('fk_id')}")
            continue
        
        try:
            udfvalue_data.append(UDFValue(
                udf_type_id=udf_type,
                fk_id=row['fk_id'],
                proj_id=proj,
                udf_date=valid_date
            ))
        except Exception as e:
            logging.warning(f"⚠️ Skipped UDFVALUE fk_id={row.get('fk_id')} due to: {e}")

    safe_bulk_create(UDFValue, udfvalue_data, "id")

    # ================== FINAL RESPONSE ==================
    return JsonResponse({
        'status': 'success',
        'message': '✅ All sheets imported successfully (invalid or duplicate rows safely skipped).'
    })

