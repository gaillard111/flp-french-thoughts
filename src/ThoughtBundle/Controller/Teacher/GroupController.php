<?php

namespace ThoughtBundle\Controller\Teacher;

use Application\Sonata\UserBundle\Entity\User;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\TeacherGroup;
use ThoughtBundle\Form\Teacher\GroupForm;
use ThoughtBundle\Form\Teacher\StudentSearchForm;

/**
 * @Route("/teacher")
 */
class GroupController extends Controller
{
    /**
     * @Route("/groups", name="teacher_groups_list")
     * @param Request $request
     * @return Response
     */
    public function groupView(Request $request)
    {
        $this->denyAccessUnlessGranted('ROLE_TEACHER', null, 'Unable to access this page!');
        $allGroups = $this->getUser()->getStudentsGroup();

        return $this->render('ThoughtBundle:teacherGroups:list.html.twig', [
            'groups' => $allGroups,
        ]);
    }

    /**
     * @Route("/group/create", name="teacher_group_create")
     * @param Request $request
     * @return Response
     */
    public function createGroup(Request $request){
        $this->denyAccessUnlessGranted('ROLE_TEACHER', null, 'Unable to access this page!');
        $teacherGroup = new TeacherGroup();
        $form = $this->createForm(new GroupForm(), $teacherGroup)
            ->add('submit', SubmitType::class,
                ['label' => 'teacher.create_group.create_button']
            );

        $form->handleRequest($request);

        if ($form->isSubmitted()) {
            $em = $this->getDoctrine()->getManager();
            $teacherGroup->setOwner($this->getUser());
            $em->persist($teacherGroup);
            $em->flush();
            return $this->redirectToRoute('teacher_group_edit', [
                'id' => $teacherGroup->getId()
            ]);
        }

        return $this->render('ThoughtBundle:teacherGroups:create.html.twig', [
            'form' => $form->createView()
        ]);
    }

    /**
     * @Route("/group/{id}/edit", name="teacher_group_edit")
     * @ParamConverter("group", options={"mapping"={"id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function editGroup(Request $request, TeacherGroup $group)
    {
        if ($group->getOwner() !== $this->getUser()) {
            throw $this->createAccessDeniedException();
        }

        $searchForm = $this->createForm(new StudentSearchForm(), null, [
            'action' => $this->generateUrl('add_student_to_group', ['id' => $group->getId()])
        ]);
        $form = $this->createForm(new GroupForm(), $group);
        $form->handleRequest($request);
        if ($form->isSubmitted()) {
            $em = $this->getDoctrine()->getManager();
            $em->persist($group);
            $em->flush();
            return $this->redirectToRoute('teacher_groups_list');
        }
        return $this->render('ThoughtBundle:teacherGroups:edit.html.twig', [
            'searchForm' => $searchForm->createView(),
            'group' => $group,
            'form' => $form->createView()
        ]);
    }

    /**
     * @Route("/group/{id}/delete", name="teacher_group_delete")
     * @ParamConverter("group", options={"mapping"={"id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function removeGroup(Request $request, TeacherGroup $group)
    {
        if ($group->getOwner() !== $this->getUser()) {
            throw $this->createAccessDeniedException();
        }

        $em = $this->getDoctrine()->getManager();
        $em->remove($group);
        $em->flush();

        return $this->redirectToRoute('teacher_groups_list');
    }

    /**
     * @Route("/group/{id}/edit/add_student", name="add_student_to_group")
     * @ParamConverter("group", options={"mapping"={"id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function addStudent(Request $request, TeacherGroup $group): Response
    {
        if ($group->getOwner() !== $this->getUser()) {
            throw $this->createAccessDeniedException();
        }

        $em = $this->getDoctrine()->getManager();
        $searchForm = $this->createForm(new StudentSearchForm());
        $searchForm->handleRequest($request);
        $user = $searchForm->getData()['searchField'];

        if (!is_null($user) and
            !$group->getStudents()->contains($user) and
            in_array('ROLE_STUDENT', $user->getRoles())
        ) {
            $group->addStudent($user);
            $em->persist($group);
            $em->flush();
        }

        return $this->redirectToRoute('teacher_group_edit', ['id' => $group->getId()]);
    }

    /**
     * @Route("/group/{group_id}/edit/remove_student/{student_id}", name="remove_student_from_group")
     * @ParamConverter("group", options={"mapping"={"group_id"="id"}})
     * @ParamConverter("user", options={"mapping"={"student_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function removeStudent(Request $request, TeacherGroup $group, User $user): Response
    {
        if ($group->getOwner() !== $this->getUser()) {
            throw $this->createAccessDeniedException();
        }

        $group->removeStudent($user);
        $em = $this->getDoctrine()->getManager();
        $em->persist($group);
        $em->flush();

        return $this->redirectToRoute('teacher_group_edit', ['id' => $group->getId()]);
    }

    /**
     * @Route("/teacher/group/search", name="student_search")
     * @param Request $request
     * @return Response
     */
    public function searchAuthor(Request $request): Response
    {
        $q = $request->query->get('q');
        $results = $this->getDoctrine()->getRepository(User::class)->getStudentsLike($q);

        return $this->render('ThoughtBundle:teacherGroups:search.json.twig', ['results' => $results]);
    }
}