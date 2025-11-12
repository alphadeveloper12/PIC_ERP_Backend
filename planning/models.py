# from django.db import models

# # Create your models here.
# class Currency(models.Model):
#     curr_id = models.IntegerField(unique=True)
#     decimal_digit_cnt = models.IntegerField()
#     curr_symbol = models.CharField(max_length=10)
#     decimal_symbol = models.CharField(max_length=5)
#     digit_group_symbol = models.CharField(max_length=5)
#     pos_curr_fmt_type = models.CharField(max_length=20, blank=True, null=True)
#     neg_curr_fmt_type = models.CharField(max_length=20, blank=True, null=True)
#     curr_type = models.CharField(max_length=50)
#     curr_short_name = models.CharField(max_length=10)
#     group_digit_cnt = models.DecimalField(max_digits=5, decimal_places=2)
#     base_exch_rate = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)

#     def __str__(self):
#         return f"{self.curr_short_name} ({self.curr_type})"

# class OBS(models.Model):
#     obs_id = models.IntegerField(unique=True)
#     parent_obs = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_obs')
#     guid = models.CharField(max_length=255, blank=True, null=True)
#     seq_num = models.IntegerField()

#     def __str__(self):
#         return f"OBS {self.obs_id} - {self.guid}"


# class Curve(models.Model):
#     curv_id = models.IntegerField(unique=True)
#     curv_name = models.CharField(max_length=255)
#     default_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     pct_usage_0 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_1 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_2 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_3 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_4 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_5 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_6 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_7 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_8 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_9 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_10 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_11 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_12 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_13 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_14 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_15 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_16 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_17 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_18 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_19 = models.DecimalField(max_digits=5, decimal_places=2)
#     pct_usage_20 = models.DecimalField(max_digits=5, decimal_places=2)

#     def __str__(self):
#         return self.curv_name

# class UDFType(models.Model):
#     udf_type_id = models.IntegerField(unique=True)
#     table_name = models.CharField(max_length=100)
#     udf_type_name = models.CharField(max_length=255)
#     udf_type_label = models.CharField(max_length=255)
#     logical_data_type = models.CharField(max_length=50)
#     super_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])

#     def __str__(self):
#         return self.udf_type_name


# class UnitOfMeasurement(models.Model):
#     unit_id = models.IntegerField(unique=True)
#     seq_num = models.IntegerField()
#     unit_abbrev = models.CharField(max_length=20)
#     unit_name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.unit_name


# class Project(models.Model):
#     proj_id = models.IntegerField(unique=True)
#     fy_start_month_num = models.IntegerField()
#     rsrc_self_add_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     allow_complete_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     rsrc_multi_assign_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     checkout_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     project_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     step_complete_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     cost_qty_recalc_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     batch_sum_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     guid = models.CharField(max_length=255, blank=True, null=True)
#     def_qty_type = models.CharField(max_length=50)
#     def_rate_type = models.CharField(max_length=50)
#     def_task_type = models.CharField(max_length=50)
#     act_pct_link_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])

#     def __str__(self):
#         return f"Project {self.proj_id}"



# class Calendar(models.Model):
#     clndr_id = models.IntegerField(unique=True)
#     default_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     clndr_name = models.CharField(max_length=255)
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Assuming it relates to the Project model
#     base_clndr_id = models.CharField(max_length=50)
#     last_chng_date = models.DateTimeField()
#     clndr_type = models.CharField(max_length=50)
#     day_hr_cnt = models.IntegerField()
#     week_hr_cnt = models.IntegerField()
#     month_hr_cnt = models.IntegerField()
#     year_hr_cnt = models.IntegerField()
#     rsrc_private = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.clndr_name



# class SchedulingOption(models.Model):
#     schedoptions_id = models.IntegerField(unique=True)
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model
#     sched_outer_depend_type = models.CharField(max_length=50)
#     sched_open_critical_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     sched_lag_early_start_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     sched_retained_logic = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     sched_setplantoforecast = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     sched_float_type = models.CharField(max_length=50)
#     sched_calendar_on_relationship_lag = models.CharField(max_length=50)
#     sched_use_expect_end_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     level_within_float_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     level_keep_sched_date_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     level_all_rsrc_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     sched_use_project_end_date_for_float = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     enable_multiple_longest_path_calc = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     limit_multiple_longest_path_calc = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     max_multiple_longest_path = models.IntegerField()
#     use_total_float_multiple_longest_paths = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     key_activity_for_multiple_longest_paths = models.IntegerField()
#     LevelPriorityList = models.TextField()

#     def __str__(self):
#         return f"Scheduling Option {self.schedoptions_id}"



# class WBS(models.Model):
#     wbs_id = models.IntegerField(unique=True)
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model
#     obs_id = models.ForeignKey(OBS, on_delete=models.CASCADE)  # Link to the OBS model
#     seq_num = models.IntegerField()
#     est_wt = models.DecimalField(max_digits=5, decimal_places=2)
#     proj_node_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     sum_data_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     status_code = models.CharField(max_length=50)
#     wbs_short_name = models.CharField(max_length=50)
#     wbs_name = models.CharField(max_length=255)
#     phase_id = models.IntegerField()
#     parent_wbs = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)  # Self-referencing FK for hierarchy
#     ev_user_pct = models.DecimalField(max_digits=5, decimal_places=2)
#     ev_etc_user_value = models.DecimalField(max_digits=10, decimal_places=4)
#     orig_cost = models.DecimalField(max_digits=10, decimal_places=2)
#     independ_remain_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
#     ann_dscnt_rate_pct = models.CharField(max_length=50)
#     dscnt_period_type = models.CharField(max_length=50)
#     independ_remain_work_qty = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.wbs_name


# class Resource(models.Model):
#     rsrc_id = models.IntegerField(unique=True)
#     parent_rsrc = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_resources')
#     clndr_id = models.ForeignKey(Calendar, on_delete=models.CASCADE)  # Link to the Calendar model
#     role_id = models.CharField(max_length=100)
#     shift_id = models.CharField(max_length=50)
#     user_id = models.CharField(max_length=100)
#     pobs_id = models.ForeignKey(OBS, on_delete=models.CASCADE)  # Link to the OBS model
#     guid = models.CharField(max_length=255)
#     rsrc_seq_num = models.IntegerField()
#     email_addr = models.CharField(max_length=100, blank=True, null=True)
#     employee_code = models.CharField(max_length=50, blank=True, null=True)
#     office_phone = models.CharField(max_length=20, blank=True, null=True)
#     other_phone = models.CharField(max_length=20, blank=True, null=True)
#     rsrc_name = models.CharField(max_length=255)
#     rsrc_short_name = models.CharField(max_length=50)
#     rsrc_title_name = models.CharField(max_length=255, blank=True, null=True)
#     def_qty_per_hr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     cost_qty_type = models.CharField(max_length=50, blank=True, null=True)

#     def __str__(self):
#         return self.rsrc_name



# class ActivityType(models.Model):
#     actv_code_type_id = models.IntegerField(unique=True)
#     actv_short_len = models.IntegerField()
#     seq_num = models.IntegerField()
#     actv_code_type = models.CharField(max_length=255)
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model
#     wbs_id = models.CharField(max_length=50)

#     def __str__(self):
#         return self.actv_code_type


# class ResourceRate(models.Model):
#     rsrc_rate_id = models.IntegerField(unique=True)
#     rsrc_id = models.ForeignKey(Resource, on_delete=models.CASCADE)  # Link to the Resource model
#     max_qty_per_hr = models.DecimalField(max_digits=5, decimal_places=2)
#     cost_per_qty = models.DecimalField(max_digits=10, decimal_places=2)
#     start_date = models.DateTimeField()
#     shift_period_id = models.DecimalField(max_digits=5, decimal_places=2)
#     cost_per_qty2 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     cost_per_qty3 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     cost_per_qty4 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

#     def __str__(self):
#         return f"Rate for Resource {self.rsrc_id}"


# class Task(models.Model):
#     task_id = models.IntegerField(unique=True)
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model
#     wbs_id = models.ForeignKey(WBS, on_delete=models.CASCADE)  # Link to the Work Breakdown Structure (WBS)
#     clndr_id = models.ForeignKey(Calendar, on_delete=models.CASCADE)  # Link to the Calendar model
#     phys_complete_pct = models.DecimalField(max_digits=5, decimal_places=2)
#     rev_fdbk_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     est_wt = models.DecimalField(max_digits=5, decimal_places=2)
#     lock_plan_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     auto_compute_act_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     complete_pct_type = models.CharField(max_length=50)
#     target_start_date = models.CharField(max_length=50)
#     target_end_date = models.CharField(max_length=50)
#     rem_late_start_date = models.TextField(blank=True, null=True)
#     rem_late_end_date = models.TextField(blank=True, null=True)
#     cstr_type = models.CharField(max_length=50)
#     priority_type = models.IntegerField()
#     suspend_date = models.DateTimeField()
#     resume_date = models.DateTimeField()
#     float_path = models.CharField(max_length=50)
#     float_path_order = models.CharField(max_length=50)

#     def __str__(self):
#         return f"Task {self.task_id} - {self.target_start_date}"



# class ActivityCode(models.Model):
#     actv_code_id = models.IntegerField(unique=True)
#     parent_actv_code = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_codes')
#     actv_code_type_id = models.ForeignKey(ActivityType, on_delete=models.CASCADE)  # Link to the ActivityType model
#     actv_code_name = models.CharField(max_length=255)
#     short_name = models.CharField(max_length=50)
#     seq_num = models.IntegerField()
#     color = models.CharField(max_length=7)  # Hex color code
#     total_assignments = models.IntegerField(blank=True, null=True)

#     def __str__(self):
#         return self.actv_code_name



# class TaskResource(models.Model):
#     taskrsrc_id = models.IntegerField(unique=True)
#     task_id = models.ForeignKey(Task, on_delete=models.CASCADE)  # Link to the Task model
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model
#     cost_qty_link_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     role_id = models.IntegerField()
#     acct_id = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
#     rsrc_id = models.ForeignKey(Resource, on_delete=models.CASCADE)  # Link to the Resource model
#     pobs_id = models.ForeignKey(OBS, on_delete=models.CASCADE)  # Link to the OBS model
#     skill_level = models.IntegerField()
#     remain_qty = models.DecimalField(max_digits=10, decimal_places=2)
#     restart_date = models.DateTimeField(blank=True, null=True)
#     target_start_date = models.DateField()
#     target_end_date = models.DateField()
#     rem_late_start_date = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     rem_late_end_date = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     rollup_dates_flag = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')])
#     remain_crv = models.DateTimeField()
#     actual_crv = models.DateTimeField(blank=True, null=True)

#     def __str__(self):
#         return f"Resource {self.rsrc_id} assigned to Task {self.task_id}"



# class TaskActivity(models.Model):
#     task_id = models.ForeignKey(Task, on_delete=models.CASCADE)  # Link to the Task model
#     actv_code_type_id = models.ForeignKey(ActivityType, on_delete=models.CASCADE)  # Link to the ActivityType model
#     actv_code_id = models.ForeignKey(ActivityCode, on_delete=models.CASCADE)  # Link to the ActivityCode model
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model

#     def __str__(self):
#         return f"Activity for Task {self.task_id} - {self.actv_code_id}"



# class UDFValue(models.Model):
#     udf_type_id = models.ForeignKey(UDFType, on_delete=models.CASCADE)  # Link to the UDFType model
#     fk_id = models.IntegerField()  # Foreign key ID, possibly linking to Task, Resource, or other entities
#     proj_id = models.ForeignKey(Project, on_delete=models.CASCADE)  # Link to the Project model
#     udf_date = models.DateTimeField()

#     def __str__(self):
#         return f"UDF Value for Project {self.proj_id}"





from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} → {self.name}"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Activity(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="activities")
    activity_id = models.CharField(max_length=100)
    activity_name = models.CharField(max_length=255, null=True, blank=True)
    original_duration = models.FloatField(null=True, blank=True)
    early_start = models.DateField(null=True, blank=True)
    early_finish = models.DateField(null=True, blank=True)
    late_start = models.DateField(null=True, blank=True)
    late_finish = models.DateField(null=True, blank=True)
    total_float = models.FloatField(null=True, blank=True)
    budgeted_total_cost = models.FloatField(null=True, blank=True)
    owner = models.CharField(max_length=255, null=True, blank=True)
    activity_location = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.activity_id
