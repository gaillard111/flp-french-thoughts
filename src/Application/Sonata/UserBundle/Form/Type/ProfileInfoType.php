<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\ChoiceType;
use Symfony\Component\Form\Extension\Core\Type\TextareaType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class ProfileInfoType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('about', TextareaType::class, [
                'label'      => 'user.form.profile.about.label',
                'label_attr' => [
                    'class' => 'control-label col-sm-2',
                ],
                'attr' => [
                    'class' => 'form-control',
                    'rows'  => '7',
                ],
                'required' => false,
            ])
            ->add('country', TextType::class, [
                'label'      => 'user.form.profile.country.label',
                'label_attr' => [
                    'class' => 'control-label col-sm-2',
                ],
                'attr' => [
                    'class' => 'form-control',
                ],
                'required' => false,
            ])
            ->add('interests', TextType::class, [
                'label'      => 'user.form.profile.interests.label',
                'label_attr' => [
                    'class' => 'control-label col-sm-2',
                ],
                'attr' => [
                    'class' => 'form-control',
                ],
                'required' => false,
            ])
            ->add('gender', ChoiceType::class, [
                'choices' => [
                    User::GENDER_MALE   => 'user.form.profile.gender.genderm',
                    User::GENDER_FEMALE => 'user.form.profile.gender.genderf',
                ],
                'label'      => 'user.form.profile.gender.label',
                'label_attr' => [
                    'class' => 'control-label col-sm-2',
                ],
                'attr' => [
                    'class' => 'form-control',
                ],
                'required' => false,
            ]);
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class'        => User::class,
            'validation_groups' => 'profileInfo',
        ]);
    }

    public function getBlockPrefix()
    {
        return 'application_sonata_user_bundle_profile_info_type';
    }
}
