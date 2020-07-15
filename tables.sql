# note: we should define the default charset of the database before creating the tables without explicitly
# defining charset

# drop database if exists ShellDesign;
# ALTER DATABASE ShellDesign CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

drop table if exists `take`;
drop table if exists `info`;
drop table if exists `teach`;
drop table if exists `attach_to`;
drop table if exists `attachment`;
drop table if exists `homework`;
drop table if exists `submission`;
drop table if exists `content`;
drop table if exists `teacher`;
drop table if exists `student`;
drop table if exists `admin`;
drop table if exists `course`;

create table `teacher`
(
    name          varchar(100),
    id            bigint primary key,
    brief         varchar(2000),
    password_hash varchar(64)
);

create table `student`
(
    name          varchar(100),
    id            bigint primary key,
    brief         varchar(2000),
    password_hash char(64)
);

create table `admin`
(
    name          varchar(100),
    id            bigint primary key,
    password_hash char(64)
);

create table `course`
(
    name_zh  varchar(100),
    name_en  varchar(100),
    brief    varchar(2000),
    syllabus varchar(4000),
    id       bigint primary key
);

create table `teach`
(
    tid bigint,
    cid bigint,
    foreign key (`tid`) references teacher (`id`),
    foreign key (`cid`) references course (`id`)
);

create table `take`
(
    cid bigint,
    sid bigint,
    foreign key (`sid`) references student (`id`),
    foreign key (`cid`) references course (`id`)
);

# this is a dummy class so that we can ensure foreign key references from attachments to both submissions and homework
create table `content`
(
    id bigint primary key
);

create table `info`
(
    id           bigint primary key,
    content      varchar(2000),
    cid          bigint,
    release_time datetime,
    foreign key (`cid`) references course (`id`),
    foreign key (`id`) references content (`id`)
);

create table `homework`
(
    id            bigint primary key,
    cid           bigint,
    tid           bigint,
    intro         varchar(2000),
    creation_time datetime,
    end_time      datetime,
    type          char(1),
    check (type in ('H', 'E')), # H for regular homework, E for experiments
    foreign key (`id`) references content (`id`),
    foreign key (`tid`) references teacher (`id`),
    foreign key (`cid`) references course (`id`)
);

create table `submission`
(
    id              bigint primary key,
    cid             bigint,
    sid             bigint,
    submission_text varchar(2000),
    creation_time   datetime,
    submission_time datetime,
    foreign key (`id`) references content (`id`),
    foreign key (`sid`) references student (`id`),
    foreign key (`cid`) references course (`id`)
);

create table `attachment`
(
    id    bigint primary key,
    name  varchar(100),
    url   varchar(800),
    brief varchar(2000)
);

create table `attach_to`
(
    aid bigint,
    uid bigint,
    foreign key (`aid`) references attachment (`id`),
    foreign key (`uid`) references content (`id`)
);

insert into `course`(id, name_zh, name_en)
values (1, '数据库系统', 'Database System'),
       (2, 'Linux程序设计', 'Linux Program Design'),
       (3, '高级数据结构与算法分析', 'Advances Data Structure and Algorithm Design'),
       (4, '计算机图形学', 'Computer Graphics'),
       (5, '视觉识别中的深度卷积神经网络', 'Convolutional Neural Network for Visual Recognition'),
       (6, 'iOS开发', 'iOS Software Development');

insert into `teacher`(id, name, password_hash)
values (1, 'zy', '49aabdaa1b0f6c3506f54521ef81fe5b5fe835d268f1f86e1021a342b59d43bc'), # password is zy
       (2, 'xz', 'b44f7d6b5283a44ee5f2bd98f84087a04810092122d75e8fbf8ad85f8f2981f1'); # password is xz

insert into `admin`(id, name, password_hash)
values (1, 'root', '53175bcc0524f37b47062fafdda28e3f8eb91d519ca0a184ca71bbebe72f969a'), # password is root
       (2, 'admin', 'fc8252c8dc55839967c58b9ad755a59b61b67c13227ddae4bd3f78a38bf394f7'); # password is admin

insert into `student`(id, name, password_hash)
values (1, 'st1', '2238ead9c048f351712c34d22b41f6eec218ea9a9e03e48fad829986b0dafc11'), # password is same as name
       (2, 'st2', '5e61d026a7889d9fc72e17f1b25f4d6d48bfe17046fea845aa8c5651ec89c333'),
       (3, 'st3', 'bbb977f8e93feb5dbd79e0688b822115b5acf774dd8a1fe6964e03d6b9579384'),
       (4, 'st4', '6133396ebcd382b137088d2ea91d60637744e404b4376e4635b45784b718db72'),
       (5, 'st5', 'd691a62aa63f1be970582902d0ff78df29899f09c5dd540b1447cdd051dcfc8d'),
       (6, 'st6', 'a7a287ffc9cb27131b9dc54199ba96cef87e753968bc620d714af212ef0f7a8c'),
       (7, 'st7', '73d0daf13c6159a1fbdeb37b6972325b6e29c312371a0f3d427bd35c0c87b928'),
       (8, 'st8', '4ce70fc1eef7303879a2ef33996db2f85058ae06e8590521267ae8d46ec59793');

insert into `teach`(cid, tid)
values (1, 1),
       (1, 2),
       (2, 1),
       (3, 1),
       (4, 2),
       (5, 2);

insert into `take`(cid, sid)
values (1, 1),
       (1, 2),
       (1, 3),
       (1, 4),
       (2, 3),
       (2, 4),
       (2, 5),
       (2, 6),
       (3, 7),
       (3, 8),
       (4, 1),
       (4, 3),
       (4, 5),
       (5, 2),
       (5, 4),
       (5, 6),
       (5, 8),
       (6, 1),
       (6, 7),
       (6, 8);