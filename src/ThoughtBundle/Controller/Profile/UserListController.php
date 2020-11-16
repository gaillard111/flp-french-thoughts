<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

class UserListController extends Controller
{
    /**
     * @Route("/students/list", name="students_list")
     * @param Request $request
     * @return Response
     */
    public function studentList(Request $request)
    {
        $this->denyAccessUnlessGranted(['ROLE_STUDENT', 'ROLE_TEACHER', 'ROLE_ADMIN'], null, 'Unable to access this page!');
        $userRepository = $this->getDoctrine()->getRepository(User::class);

        $studentsQuery = $userRepository->getAllStudentsQuery();

        $paginator  = $this->get('knp_paginator');
        $paginationStudents = $paginator->paginate(
            $studentsQuery,
            $request->query->getInt('page', 1),
            20
        );

        return $this->render('@Thought/Profile/students_list.html.twig', [
            'students' => $paginationStudents,
        ]);
    }

    /**
     * @Route("/teachers/list", name="teachers_list")
     * @param Request $request
     * @return Response
     */
    public function teachersList(Request $request)
    {
        $this->denyAccessUnlessGranted(['ROLE_TEACHER', 'ROLE_ADMIN'], null, 'Unable to access this page!');
        $userRepository = $this->getDoctrine()->getRepository(User::class);

        $teachersQuery = $userRepository->getAllTeachersQuery();

        $paginator  = $this->get('knp_paginator');
        $paginationTeachers = $paginator->paginate(
            $teachersQuery,
            $request->query->getInt('page', 1),
            20
        );

        return $this->render('@Thought/Profile/teachers_list.twig', [
            'teachers' => $paginationTeachers,
        ]);
    }
}